import uvicorn
from app.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        reload_dirs=["app"] if settings.debug else None,
        reload_excludes=["venv", "tests", ".pytest_cache", "__pycache__"] if settings.debug else None,
    )
