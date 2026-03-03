import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.scenarios import SCENARIOS  # single source of truth

pytestmark = pytest.mark.asyncio


async def test_health_check():
    """Test the health check endpoint — no API key required."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.skip(
    reason="Requires a valid OPENAI_API_KEY or local Qwen model weights. "
           "Run manually: pytest tests/ -k test_generate_ecommerce"
)
async def test_generate_ecommerce():
    """Test generating an e-commerce backend architecture."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/generate", json={"requirement": SCENARIOS["E-commerce backend"]})

    assert response.status_code == 200
    data = response.json()
    assert "blueprint" in data
    assert "metrics" in data
    assert "token_usage" in data
    assert "recommended_stack" in data["blueprint"]
    assert 1 <= data["metrics"]["final_metric_score"] <= 10000


@pytest.mark.skip(
    reason="Requires a valid OPENAI_API_KEY or local Qwen model weights."
)
async def test_generate_edtech():
    """Test generating an EdTech backend architecture."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/generate", json={"requirement": SCENARIOS["EdTech exam platform"]})

    assert response.status_code == 200
    data = response.json()
    assert "blueprint" in data
    assert len(data["blueprint"]["api_routes"]) > 0
    assert len(data["blueprint"]["database_schema"]) > 0


@pytest.mark.skip(
    reason="Requires a valid OPENAI_API_KEY or local Qwen model weights."
)
async def test_generate_ai_saas():
    """Test generating an AI SaaS backend architecture."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/generate", json={"requirement": SCENARIOS["AI SaaS product"]})

    assert response.status_code == 200
    data = response.json()
    assert "blueprint" in data
    stack = data["blueprint"]["recommended_stack"]
    assert "database" in stack
