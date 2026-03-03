"""
Local offline inference using Qwen/Qwen2-1.5B-Instruct via HuggingFace Transformers.

This module is used automatically by agent.py when no OPENAI_API_KEY is configured.
The model is loaded lazily (only once) and runs on GPU (CUDA/MPS) when available,
falling back to CPU otherwise.
"""

import json
import re
import time
from typing import Optional, Tuple

from app.config import settings
from app.utils import logger
from app.tools import ArchitectureBlueprint
from app.prompts import ARCHITECTURE_AGENT_SYSTEM_PROMPT, USER_REQUIREMENT_PROMPT

_tokenizer = None
_model = None
_device: Optional[str] = None


def _get_device() -> str:
    """Return 'cuda', 'mps', or 'cpu' depending on what is available."""
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
    except ImportError:
        pass
    return "cpu"


def _load_model():
    """
    Lazily load the Qwen tokenizer and model into global variables.
    Downloads weights from HuggingFace on first call (~3 GB, cached locally).
    """
    global _tokenizer, _model, _device

    if _model is not None:
        return 

    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        import torch
    except ImportError as exc:
        raise RuntimeError(
            "The 'transformers' and 'torch' packages are required for local inference. "
            "Run:  pip install transformers torch accelerate"
        ) from exc

    _device = _get_device()
    model_id = settings.local_model_name
    logger.info(f"Loading local model '{model_id}' on device='{_device}' (first-time download may take a few minutes) ...")

    # Apply HuggingFace token if configured — suppresses the unauthenticated warning
    # and enables higher rate limits for model downloads.
    if settings.hf_token:
        import os
        os.environ["HF_TOKEN"] = settings.hf_token

    _tokenizer = AutoTokenizer.from_pretrained(model_id)

    _model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype="auto",      
        device_map=_device,    
    )
    _model.eval()
    logger.info(f"Local model '{model_id}' loaded successfully on {_device}.")


def _extract_json(text: str) -> Optional[dict]:
    """
    Try to extract a JSON object from raw model output.

    Strategy:
      1. Direct json.loads on the full text.
      2. Find the first {...} block via regex and parse that.
    """
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]+\}", text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return None


def _normalize_blueprint_dict(raw: dict) -> dict:
    """
    Coerce a raw model-output dict to match the ArchitectureBlueprint schema.

    Small models frequently produce structurally creative but non-conformant JSON:
      - database_schema wrapped in {'entities': [...]} instead of a bare list
      - deployment_recommendations / scaling_recommendations as dicts instead of strings
    """
    # --- database_schema: unwrap if the model wrapped it in a dict ---
    db = raw.get("database_schema")
    if isinstance(db, dict):
        for key in ("entities", "tables", "collections", "schema", "models"):
            if key in db and isinstance(db[key], list):
                raw["database_schema"] = db[key]
                break
        else:
            raw["database_schema"] = []  # nothing salvageable

    # --- text fields: flatten dict → readable string ---
    def _dict_to_str(value: dict) -> str:
        parts = []
        for k, v in value.items():
            if isinstance(v, dict):
                inner = ", ".join(f"{ik}={iv}" for ik, iv in v.items())
                parts.append(f"{k}: {inner}")
            elif isinstance(v, list):
                parts.append(f"{k}: {', '.join(str(i) for i in v)}")
            else:
                parts.append(f"{k}: {v}")
        return ". ".join(parts)

    for field in ("deployment_recommendations", "scaling_recommendations"):
        value = raw.get(field)
        if isinstance(value, dict):
            raw[field] = _dict_to_str(value)
        elif isinstance(value, list):
            raw[field] = ". ".join(str(item) for item in value)

    # --- database entities: ensure relationships always present ---
    db_list = raw.get("database_schema", [])
    if isinstance(db_list, list):
        for entity in db_list:
            if isinstance(entity, dict):
                # relationships is often omitted by small models — default to []
                if "relationships" not in entity:
                    entity["relationships"] = []
                # If relationships is a dict or string, normalise to a list
                rel = entity["relationships"]
                if isinstance(rel, dict):
                    entity["relationships"] = [f"{k}: {v}" for k, v in rel.items()]
                elif isinstance(rel, str):
                    entity["relationships"] = [rel] if rel.strip() else []

    return raw



async def generate_architecture_local(
    requirement: str,
) -> Tuple[Optional[ArchitectureBlueprint], float, dict]:
    """
    Generate a backend architecture blueprint using the local Qwen2 model.

    Args:
        requirement: Plain-English product requirement string.

    Returns:
        Tuple of (blueprint | None, latency_seconds, token_usage_dict).
    """
    import asyncio

    _load_model()

    messages = [
        {"role": "system", "content": ARCHITECTURE_AGENT_SYSTEM_PROMPT},
        {"role": "user",   "content": USER_REQUIREMENT_PROMPT.format(requirement=requirement)},
    ]

    import torch

    start = time.time()
    usage_dict = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    try:
        inputs = _tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        ).to(_device)

        prompt_len = inputs["input_ids"].shape[-1]
        usage_dict["prompt_tokens"] = int(prompt_len)

        loop = asyncio.get_event_loop()

        def _generate():
            with torch.no_grad():
                return _model.generate(
                    **inputs,
                    max_new_tokens=settings.local_model_max_tokens,
                    do_sample=False,         
                    temperature=None,
                    top_p=None,
                    pad_token_id=_tokenizer.eos_token_id,
                )

        outputs = await loop.run_in_executor(None, _generate)

        new_tokens = outputs[0][prompt_len:]
        completion_text = _tokenizer.decode(new_tokens, skip_special_tokens=True)

        latency = time.time() - start

        completion_len = len(new_tokens)
        usage_dict["completion_tokens"] = int(completion_len)
        usage_dict["total_tokens"]      = int(prompt_len + completion_len)

        logger.info(f"Local model generated {completion_len} tokens in {latency:.2f}s")
        logger.debug(f"Raw local model output (first 500 chars):\n{completion_text[:500]}")

        raw_dict = _extract_json(completion_text)
        if raw_dict is None:
            logger.error("Local model output did not contain parseable JSON.")
            return None, latency, usage_dict

        # Coerce non-conformant structures before Pydantic validation
        raw_dict = _normalize_blueprint_dict(raw_dict)
        blueprint = ArchitectureBlueprint.model_validate(raw_dict)
        logger.info("Successfully parsed ArchitectureBlueprint from local model output.")
        return blueprint, latency, usage_dict

    except Exception as exc:
        latency = time.time() - start
        logger.error(f"Local model inference error: {exc}")
        return None, latency, usage_dict
