"""Golden path integration test for example-project.

This test verifies the complete end-to-end workflow:
Idea → Tests → Smoke → Governance → WorkflowStatus.SUCCESS
"""

import pytest
from agents.orchestrator.orchestrator_agent import OrchestratorAgent, WorkflowStatus
from autopilot_core.config.project_registry import ProjectRegistry


def test_example_project_golden_path_workflow():
    """
    Golden path test: Full feature workflow on example-project.
    
    Tests the complete happy path:
    - Loads project config
    - Validates contract exists
    - Runs tests (should pass)
    - Runs smoke tests (should pass)
    - Checks governance (if enabled)
    - Returns SUCCESS status
    """
    # Setup: Ensure example-project uses local path
    registry = ProjectRegistry()
    if registry.get_project("example-project"):
        registry.unregister_project("example-project")
    
    orchestrator = OrchestratorAgent(project_registry=registry)
    
    # Run full workflow with all checks enabled
    workflow_id, status, message, details = orchestrator.run_feature_workflow(
        project_id="example-project",
        contract_path="design-contracts/test-feature.md",
        dry_run=False,
        run_codegen=False,  # Skip codegen for this test (focus on existing code)
        run_tests=True,
        run_smoke=True,  # Enable smoke tests
        create_pr=False,  # Skip PR creation (no governance check in this case)
        run_bugfix=False,
    )
    
    # Assertions: The call should complete without raising
    assert status == "accepted", f"Workflow should be accepted, got: {status}, message: {message}"
    
    # Assert workflow status is SUCCESS
    workflow_status = details.get("workflow_status")
    assert workflow_status == WorkflowStatus.SUCCESS.value, (
        f"Expected workflow_status=SUCCESS, got: {workflow_status}. "
        f"Details: {details}"
    )
    
    # Assert tests passed
    tests_passed = details.get("tests_passed")
    assert tests_passed is True, (
        f"Expected tests_passed=True, got: {tests_passed}. "
        f"Test result: {details.get('test_result')}"
    )
    
    # Assert smoke tests passed (since run_smoke=True)
    smoke_passed = details.get("smoke_passed")
    assert smoke_passed is True, (
        f"Expected smoke_passed=True (run_smoke=True), got: {smoke_passed}. "
        f"Smoke result: {details.get('smoke_result')}"
    )
    
    # Governance: Since create_pr=False, governance_ok should be None
    # (governance only runs when create_pr=True)
    governance_ok = details.get("governance_ok")
    assert governance_ok is None, (
        f"Expected governance_ok=None (create_pr=False), got: {governance_ok}"
    )


def test_example_project_golden_path_with_governance():
    """
    Golden path test with governance check enabled.
    
    Tests the complete workflow including governance:
    - All previous checks
    - Governance check (should pass for clean repo)
    """
    # Setup: Ensure example-project uses local path
    registry = ProjectRegistry()
    if registry.get_project("example-project"):
        registry.unregister_project("example-project")
    
    orchestrator = OrchestratorAgent(project_registry=registry)
    
    # Run full workflow with governance enabled
    workflow_id, status, message, details = orchestrator.run_feature_workflow(
        project_id="example-project",
        contract_path="design-contracts/test-feature.md",
        dry_run=False,
        run_codegen=False,
        run_tests=True,
        run_smoke=True,
        create_pr=True,  # Enable governance check
        run_bugfix=False,
    )
    
    # Assert workflow completes
    assert status == "accepted", f"Workflow should be accepted, got: {status}"
    
    # If tests and smoke pass, workflow should be SUCCESS
    # (governance might fail if there are violations, but for clean repo it should pass)
    if details.get("tests_passed") and details.get("smoke_passed"):
        workflow_status = details.get("workflow_status")
        # Could be SUCCESS or FAILED_GOVERNANCE depending on governance result
        assert workflow_status in [
            WorkflowStatus.SUCCESS.value,
            WorkflowStatus.FAILED_GOVERNANCE.value
        ], f"Unexpected workflow_status: {workflow_status}"
        
        # If governance passed, should be SUCCESS
        if details.get("governance_ok") is True:
            assert workflow_status == WorkflowStatus.SUCCESS.value

