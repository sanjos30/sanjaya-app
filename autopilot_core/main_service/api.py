"""FastAPI service with endpoints for Sanjaya Autopilot."""

from enum import Enum
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Literal, List, Optional
from agents.orchestrator.orchestrator_agent import OrchestratorAgent
from agents.product.product_agent import ProductAgent
from agents.monitor.monitor_agent import MonitorAgent, MonitorResult, MonitorIssue
from autopilot_core.config.project_registry import ProjectRegistry
from pathlib import Path


class WorkflowStatus(str, Enum):
    """Workflow execution status."""
    SUCCESS = "success"
    FAILED_TESTS = "failed_tests"
    FAILED_SMOKE = "failed_smoke"
    FAILED_GOVERNANCE = "failed_governance"
    ERROR = "error"


class WorkflowType(str, Enum):
    """Workflow type."""
    FEATURE = "feature"
    BUGFIX = "bugfix"

app = FastAPI(title="Sanjaya Autopilot API")
project_registry = ProjectRegistry()
orchestrator = OrchestratorAgent(project_registry=project_registry)
product_agent = ProductAgent(project_registry=project_registry)
monitor_agent = MonitorAgent()


class WorkflowRunRequest(BaseModel):
    """Request model for running a workflow."""
    workflow_type: str = "feature"  # Accepts "feature", "bugfix", or legacy "feature_from_contract"
    project_id: str
    contract_path: Optional[str] = None  # Required for FEATURE, optional for BUGFIX
    dry_run: bool = True
    run_codegen: bool = False
    run_tests: bool = False
    create_pr: bool = False
    branch_name: Optional[str] = None
    commit_message: Optional[str] = None
    push_branch: bool = False
    pr_base: str = "main"
    pr_title: Optional[str] = None
    pr_body: Optional[str] = None
    run_smoke: bool = False
    smoke_timeout: int = 60
    smoke_health_path: str = "/health"
    run_bugfix: bool = False


class WorkflowRunResponse(BaseModel):
    """Response model for workflow execution."""
    workflow_id: str
    status: Literal["accepted", "rejected", "error"]  # Legacy status for backward compat
    message: str
    details: Dict[str, Any]
    workflow_status: Optional[WorkflowStatus] = None  # New detailed status
    tests_passed: Optional[bool] = None
    smoke_passed: Optional[bool] = None
    governance_ok: Optional[bool] = None


class FeatureIdeaRequest(BaseModel):
    """Request model for creating a feature design contract."""
    project_id: str
    feature_name: str
    summary: str
    problem: str
    user_story: str
    notes: str = ""


class FeatureIdeaSimpleRequest(BaseModel):
    """Request model for creating a feature design contract from a simple idea."""
    project_id: str
    idea: str  # Simple feature idea description
    context: Optional[Dict[str, Any]] = None  # Additional context


class FeatureIdeaResponse(BaseModel):
    """Response model for feature design contract creation."""
    project_id: str
    contract_path: str
    message: str


class ProjectRegisterRequest(BaseModel):
    """Request model for registering a project."""
    project_id: str
    repo_url: str
    metadata: Optional[Dict[str, Any]] = None


class ProjectRegisterResponse(BaseModel):
    """Response model for project registration."""
    project_id: str
    repo_url: str
    message: str


class ProjectInfo(BaseModel):
    """Project information model."""
    project_id: str
    repo_url: str
    metadata: Dict[str, Any]


class MonitorCheckRequest(BaseModel):
    """Request model for monitoring log files."""
    log_paths: List[str]  # Relative to project root or absolute paths
    max_lines: int = 2000  # Maximum lines to read per file


class MonitorIssueResponse(BaseModel):
    """Response model for a single monitor issue."""
    severity: str
    code: str
    message: str
    line: str
    line_number: Optional[int]
    file_path: str


class MonitorCheckResponse(BaseModel):
    """Response model for monitor check."""
    issues: List[MonitorIssueResponse]
    summary: str


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        dict: Status information
    """
    return {"status": "healthy"}


@app.get("/projects", response_model=List[ProjectInfo])
async def list_projects():
    """
    List all registered projects.
    
    Returns:
        List[ProjectInfo]: List of registered projects
    """
    projects = project_registry.list_projects()
    return [ProjectInfo(**project) for project in projects]


@app.post("/projects/register", response_model=ProjectRegisterResponse)
def register_project(req: ProjectRegisterRequest):
    """
    Register a new project with Sanjaya.
    
    Args:
        req: Project registration request
        
    Returns:
        ProjectRegisterResponse: Registration confirmation
    """
    try:
        project_info = project_registry.register_project(
            project_id=req.project_id,
            repo_url=req.repo_url,
            metadata=req.metadata
        )
        
        return ProjectRegisterResponse(
            project_id=project_info["project_id"],
            repo_url=project_info["repo_url"],
            message=f"Project '{req.project_id}' registered successfully."
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/workflows/run", response_model=WorkflowRunResponse)
def run_workflow(req: WorkflowRunRequest):
    try:
        # Handle backward compatibility: "feature_from_contract" -> FEATURE
        workflow_type = req.workflow_type
        if isinstance(workflow_type, str):
            if workflow_type == "feature_from_contract":
                workflow_type = WorkflowType.FEATURE
            elif workflow_type == "feature":
                workflow_type = WorkflowType.FEATURE
            elif workflow_type == "bugfix":
                workflow_type = WorkflowType.BUGFIX
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported workflow_type: {workflow_type}")
        
        if workflow_type == WorkflowType.FEATURE:
            if not req.contract_path:
                raise HTTPException(status_code=400, detail="contract_path required for FEATURE workflow")
            wf_id, status, msg, details = orchestrator.run_feature_workflow(
                project_id=req.project_id,
                contract_path=req.contract_path,
                dry_run=req.dry_run,
                run_codegen=req.run_codegen,
                run_tests=req.run_tests,
                create_pr=req.create_pr,
                branch_name=req.branch_name,
                commit_message=req.commit_message,
                push_branch=req.push_branch,
                pr_base=req.pr_base,
                pr_title=req.pr_title,
                pr_body=req.pr_body,
                run_smoke=req.run_smoke,
                smoke_timeout=req.smoke_timeout,
                smoke_health_path=req.smoke_health_path,
                run_bugfix=req.run_bugfix,
            )
        elif workflow_type == WorkflowType.BUGFIX:
            wf_id, status, msg, details = orchestrator.run_bugfix_workflow(
                project_id=req.project_id,
                run_tests=req.run_tests,
                run_bugfix=req.run_bugfix,
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported workflow_type: {workflow_type}")

        # Extract new status fields from details
        workflow_status = details.get("workflow_status")
        tests_passed = details.get("tests_passed")
        smoke_passed = details.get("smoke_passed")
        governance_ok = details.get("governance_ok")

        return WorkflowRunResponse(
            workflow_id=wf_id,
            status=status,
            message=msg,
            details=details,
            workflow_status=workflow_status,
            tests_passed=tests_passed,
            smoke_passed=smoke_passed,
            governance_ok=governance_ok
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ideas/feature", response_model=FeatureIdeaResponse)
def create_feature_idea(req: FeatureIdeaRequest):
    """
    Create a feature design contract from structured feature idea.
    
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


@app.post("/ideas/feature-from-idea", response_model=FeatureIdeaResponse)
def create_feature_from_idea(req: FeatureIdeaSimpleRequest):
    """
    Create a comprehensive feature design contract from a simple idea using LLM.
    
    Takes a simple feature idea string and uses LLM to generate a full design contract
    with API design, data models, logging, monitoring, tests, and all sections.
    
    Returns:
        FeatureIdeaResponse: Contains project_id, contract_path, and message
    """
    try:
        result = product_agent.create_feature_contract_from_idea(
            project_id=req.project_id,
            idea=req.idea,
            context=req.context
        )
        
        return FeatureIdeaResponse(
            project_id=result["project_id"],
            contract_path=result["contract_path"],
            message="Feature design contract generated using LLM."
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/monitor/check", response_model=MonitorCheckResponse)
def check_monitor(req: MonitorCheckRequest):
    """
    Analyze log files for issues (on-demand monitoring).
    
    This endpoint:
    - Reads specified log files
    - Detects error patterns (ERROR, Exception, Traceback, HTTP 5xx, etc.)
    - Returns structured issues with severity and location
    
    Note: This is on-demand only. It does NOT automatically trigger workflows.
    
    Args:
        req: Monitor check request with log paths
        
    Returns:
        MonitorCheckResponse: Analysis result with issues and summary
    """
    try:
        # Resolve log file paths (support both absolute and relative)
        log_files = []
        for log_path_str in req.log_paths:
            log_path = Path(log_path_str)
            # If relative, try to resolve from current working directory
            if not log_path.is_absolute():
                log_path = Path.cwd() / log_path
            log_files.append(log_path)
        
        # Analyze logs
        result = monitor_agent.analyze_logs(log_files, max_lines=req.max_lines)
        
        # Convert to response model
        return MonitorCheckResponse(
            issues=[
                MonitorIssueResponse(
                    severity=issue.severity,
                    code=issue.code,
                    message=issue.message,
                    line=issue.line,
                    line_number=issue.line_number,
                    file_path=issue.file_path
                )
                for issue in result.issues
            ],
            summary=result.summary
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
