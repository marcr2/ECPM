"""FastAPI application entrypoint."""

from fastapi import FastAPI

app = FastAPI(
    title="ECPM API",
    description="Economic Crisis Prediction Model API",
    version="0.1.0",
)


@app.get("/health")
async def health() -> dict:
    """Health check endpoint used by Docker Compose."""
    return {"status": "ok"}
