"""FastAPI service with endpoints for Sanjaya Autopilot."""

from fastapi import FastAPI

app = FastAPI(title="Sanjaya Autopilot API")


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        dict: Status information
    """
    return {"status": "healthy"}


@app.get("/projects")
async def list_projects():
    """
    List all registered projects.
    
    Returns:
        dict: List of projects
    """
    pass


@app.post("/workflows/run")
async def run_workflow():
    """
    Trigger a workflow execution.
    
    Returns:
        dict: Workflow execution result
    """
    pass

