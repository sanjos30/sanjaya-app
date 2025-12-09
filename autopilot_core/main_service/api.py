"""FastAPI service with endpoints for Sanjaya Autopilot."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Literal
from agents.orchestrator.orchestrator_agent import OrchestratorAgent
from agents.product.product_agent import ProductAgent

app = FastAPI(title="Sanjaya Autopilot API")
orchestrator = OrchestratorAgent()
product_agent = ProductAgent()


class WorkflowRunRequest(BaseModel):
    """Request model for running a workflow."""
    workflow_type: str
    project_id: str
    contract_path: str
    dry_run: bool = True


class WorkflowRunResponse(BaseModel):
    """Response model for workflow execution."""
    workflow_id: str
    status: Literal["accepted", "rejected", "error"]
    message: str
    details: Dict[str, Any]


class FeatureIdeaRequest(BaseModel):
    """Request model for creating a feature design contract."""
    project_id: str
    feature_name: str
    summary: str
    problem: str
    user_story: str
    notes: str = ""


class FeatureIdeaResponse(BaseModel):
    """Response model for feature design contract creation."""
    project_id: str
    contract_path: str
    message: str


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


@app.post("/workflows/run", response_model=WorkflowRunResponse)
def run_workflow(req: WorkflowRunRequest):
    try:
        if req.workflow_type == "feature_from_contract":
            wf_id, status, msg, details = orchestrator.run_feature_workflow(
                project_id=req.project_id,
                contract_path=req.contract_path,
                dry_run=req.dry_run
            )
        else:
            raise HTTPException(status_code=400, detail="Unsupported workflow_type")

        return WorkflowRunResponse(
            workflow_id=wf_id,
            status=status,
            message=msg,
            details=details
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ideas/feature", response_model=FeatureIdeaResponse)
def create_feature_idea(req: FeatureIdeaRequest):
    """
    Create a feature design contract from a feature idea.
    
    Returns:
        FeatureIdeaResponse: Contains project_id, contract_path, and message
    """
    try:
        result = product_agent.create_feature_contract(
            project_id=req.project_id,
            feature_name=req.feature_name,
            summary=req.summary,
            problem=req.problem,
            user_story=req.user_story,
            notes=req.notes
        )
        
        return FeatureIdeaResponse(
            project_id=result["project_id"],
            contract_path=result["contract_path"],
            message="Feature design contract created."
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
