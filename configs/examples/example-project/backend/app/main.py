"""FastAPI application for example-project."""

from fastapi import FastAPI

app = FastAPI(title="Example Project", version="1.0.0")


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/ping")
def ping():
    """Simple ping endpoint for testing."""
    return {"message": "pong"}

