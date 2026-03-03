"""
Core agent: generates a backend architecture blueprint.
Routing logic:
  - If settings.openai_api_key is set   → use OpenAI gpt-4o (structured outputs)
  - If settings.openai_api_key is empty → fall back to local Qwen2 model (CPU/GPU)
"""

import time
from typing import Optional, Tuple

from pydantic import ValidationError

from app.config import settings
from app.utils import logger
from app.prompts import ARCHITECTURE_AGENT_SYSTEM_PROMPT, USER_REQUIREMENT_PROMPT
from app.tools import ArchitectureBlueprint

_openai_client = None

def _get_openai_client():
    global _openai_client
    if _openai_client is not None:
        return _openai_client
    if not settings.openai_api_key:
        return None
    try:
        from openai import AsyncOpenAI
        _openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
        return _openai_client
    except ImportError:
        logger.warning("openai package not installed; will use local model.")
        return None


async def _generate_via_openai(requirement: str) -> Tuple[Optional[ArchitectureBlueprint], float, dict]:
    client = _get_openai_client()
    start = time.time()
    usage_dict = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    try:
        response = await client.beta.chat.completions.parse(
            model=settings.model_name,
            messages=[
                {"role": "system", "content": ARCHITECTURE_AGENT_SYSTEM_PROMPT},
                {"role": "user",   "content": USER_REQUIREMENT_PROMPT.format(requirement=requirement)},
            ],
            response_format=ArchitectureBlueprint,
            temperature=0.4,
            max_tokens=4000,
        )
        latency = time.time() - start

        if response.usage:
            usage_dict = {
                "prompt_tokens":      response.usage.prompt_tokens,
                "completion_tokens":  response.usage.completion_tokens,
                "total_tokens":       response.usage.total_tokens,
            }

        message = response.choices[0].message
        if message.parsed:
            logger.info("OpenAI: successfully generated and parsed architecture blueprint.")
            return message.parsed, latency, usage_dict
        elif message.refusal:
            logger.warning(f"OpenAI model refused the request: {message.refusal}")
            return None, latency, usage_dict
        else:
            logger.error("OpenAI: failed to parse the structured output.")
            return None, latency, usage_dict

    except ValidationError as exc:
        latency = time.time() - start
        logger.error(f"Pydantic validation error mapping OpenAI output: {exc}")
        return None, latency, usage_dict
    except Exception as exc:
        latency = time.time() - start
        logger.error(f"OpenAI API call error: {exc}")
        return None, latency, usage_dict


async def generate_architecture(
    requirement: str,
) -> Tuple[Optional[ArchitectureBlueprint], float, dict]:
    logger.info(f"generate_architecture called. Requirement: {requirement[:60]}...")

    if settings.openai_api_key:
        logger.info("OPENAI_API_KEY detected — using OpenAI backend.")
        return await _generate_via_openai(requirement)
    else:
        logger.info("No OPENAI_API_KEY — using local Qwen2 model as fallback.")
        from app.local_agent import generate_architecture_local
        return await generate_architecture_local(requirement)
