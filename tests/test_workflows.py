"""Tests for workflow status computation and bugfix workflow."""

import pytest
from agents.orchestrator.orchestrator_agent import WorkflowStatus


def test_workflow_status_computation():
    """Test workflow status computation logic."""
    from agents.orchestrator.orchestrator_agent import OrchestratorAgent
    
    orchestrator = OrchestratorAgent()
    
    # Test: tests failed -> FAILED_TESTS
    status = orchestrator._compute_workflow_status(
        tests_passed=False,
        run_tests=True,
        smoke_passed=None,
        run_smoke=False,
        governance_ok=None,
        create_pr=False
    )
    assert status == WorkflowStatus.FAILED_TESTS
    
    # Test: tests passed, smoke failed -> FAILED_SMOKE
    status = orchestrator._compute_workflow_status(
        tests_passed=True,
        run_tests=True,
        smoke_passed=False,
        run_smoke=True,
        governance_ok=None,
        create_pr=False
    )
    assert status == WorkflowStatus.FAILED_SMOKE
    
    # Test: tests & smoke passed, governance failed -> FAILED_GOVERNANCE
    status = orchestrator._compute_workflow_status(
        tests_passed=True,
        run_tests=True,
        smoke_passed=True,
        run_smoke=True,
        governance_ok=False,
        create_pr=True
    )
    assert status == WorkflowStatus.FAILED_GOVERNANCE
    
    # Test: everything passed -> SUCCESS
    status = orchestrator._compute_workflow_status(
        tests_passed=True,
        run_tests=True,
        smoke_passed=True,
        run_smoke=True,
        governance_ok=True,
        create_pr=True
    )
    assert status == WorkflowStatus.SUCCESS
    
    # Test: tests not run, smoke passed -> SUCCESS
    status = orchestrator._compute_workflow_status(
        tests_passed=None,
        run_tests=False,
        smoke_passed=True,
        run_smoke=True,
        governance_ok=None,
        create_pr=False
    )
    assert status == WorkflowStatus.SUCCESS

