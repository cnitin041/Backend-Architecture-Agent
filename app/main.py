from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from app.agent import generate_architecture
from app.evaluator import evaluate_blueprint
from app.utils import logger
from app.tools import ArchitectureBlueprint
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not settings.openai_api_key:
        logger.info(
            f"No OPENAI_API_KEY detected — preloading local model "
            f"'{settings.local_model_name}' at startup (this may take a moment on first run)..."
        )
        from app.local_agent import _load_model
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _load_model)
        logger.info("Local model preloaded and ready — server is accepting requests.")
    else:
        logger.info(f"OPENAI_API_KEY detected — will use OpenAI '{settings.model_name}'.")

    yield 

    logger.info("Server shutting down.")


app = FastAPI(
    title="Backend Architecture Agent",
    description="An AI Agent that generates backend architecture blueprints based on product requirements.",
    version="1.0.0",
    lifespan=lifespan,
)


class RequirementRequest(BaseModel):
    requirement: str


class BlueprintResponse(BaseModel):
    blueprint: ArchitectureBlueprint
    metrics: Dict[str, float]
    token_usage: Dict[str, int]


@app.post("/generate", response_model=BlueprintResponse)
async def generate_architecture_endpoint(request: RequirementRequest):
    """
    Generate a full backend architecture blueprint from a product requirement string.
    """
    logger.info("Received API request to generate architecture.")

    blueprint, latency, usage = await generate_architecture(request.requirement)

    if blueprint is None:
        logger.error("Failed to generate blueprint.")
        raise HTTPException(status_code=500, detail="Agent failed to structuralize the architecture.")

    metrics = evaluate_blueprint(blueprint, latency)

    return BlueprintResponse(
        blueprint=blueprint,
        metrics=metrics,
        token_usage=usage,
    )


@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok"}
