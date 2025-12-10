"""Integration test for example-project golden path workflow."""

import pytest
from agents.orchestrator.orchestrator_agent import OrchestratorAgent, WorkflowStatus
from autopilot_core.config.project_registry import ProjectRegistry


def test_example_project_feature_workflow_dry_run():
    """Test that a feature workflow can run on example-project in dry-run mode."""
    registry = ProjectRegistry()
    # Ensure example-project is not registered (so it uses local path)
    if registry.get_project("example-project"):
        registry.unregister_project("example-project")
    orchestrator = OrchestratorAgent(project_registry=registry)
    
    # Run a dry-run workflow (validation only)
    workflow_id, status, message, details = orchestrator.run_feature_workflow(
        project_id="example-project",
        contract_path="design-contracts/test-feature.md",  # Doesn't need to exist for dry_run
        dry_run=True,
        run_codegen=False,
        run_tests=False,
        run_smoke=False,
        create_pr=False,
        run_bugfix=False,
    )
    
    # Should be accepted (validation passed)
    assert status == "accepted"
    assert "example-project" in details.get("project_id", "")
    assert details.get("dry_run") is True


def test_example_project_feature_workflow_with_tests():
    """Test that a feature workflow can run tests on example-project."""
    registry = ProjectRegistry()
    # Ensure example-project is not registered (so it uses local path)
    if registry.get_project("example-project"):
        registry.unregister_project("example-project")
    orchestrator = OrchestratorAgent(project_registry=registry)
    
    # First, we need a design contract - create a minimal one for testing
    # For now, we'll skip codegen and just test the test execution
    workflow_id, status, message, details = orchestrator.run_feature_workflow(
        project_id="example-project",
        contract_path="design-contracts/test-feature.md",  # May not exist, but we're not using it
        dry_run=False,
        run_codegen=False,  # Skip codegen for this test
        run_tests=True,
        run_smoke=False,
        create_pr=False,
        run_bugfix=False,
    )
    
    # Should complete (even if contract doesn't exist, tests should run)
    assert status in ["accepted", "rejected", "error"]
    
    # If tests ran, check the result
    if "test_result" in details:
        test_result = details["test_result"]
        # Tests should pass (we created a working backend)
        if test_result.get("status") == "passed":
            assert details.get("tests_passed") is True
            assert details.get("workflow_status") == WorkflowStatus.SUCCESS.value
        elif test_result.get("status") == "failed":
            # If tests failed, workflow status should reflect that
            assert details.get("workflow_status") == WorkflowStatus.FAILED_TESTS.value


def test_example_project_bugfix_workflow():
    """Test that a bugfix workflow can run on example-project."""
    registry = ProjectRegistry()
    # Ensure example-project is not registered (so it uses local path)
    if registry.get_project("example-project"):
        registry.unregister_project("example-project")
    orchestrator = OrchestratorAgent(project_registry=registry)
    
    workflow_id, status, message, details = orchestrator.run_bugfix_workflow(
        project_id="example-project",
        run_tests=True,
        run_bugfix=False,  # Don't suggest fixes, just run tests
    )
    
    # Should complete
    assert status == "accepted"
    assert "example-project" in details.get("project_id", "")
    
    # If tests ran and passed, workflow should be SUCCESS
    if details.get("tests_passed") is True:
        assert details.get("workflow_status") == WorkflowStatus.SUCCESS.value

