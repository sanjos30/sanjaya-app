"""Tests for ProductAgent refinements: locked intent, confidence, out_of_scope, snapshot."""

import pytest
from unittest.mock import Mock, patch
from agents.product.product_agent import ProductAgent
from autopilot_core.config.loader import ConfigLoader
from autopilot_core.config.project_registry import ProjectRegistry


def test_locked_intent_prevents_contract_creation():
    """Test that locked intent prevents ProductAgent from creating contracts."""
    from unittest.mock import MagicMock
    
    registry = ProjectRegistry()
    # Create ProductAgent without LLM client to avoid API calls
    product_agent = ProductAgent(project_registry=registry, llm_client=None)
    
    # Mock questionnaire with locked intent
    questionnaire = {
        "intent": {"locked": True},
        "project_type": {"value": "demo"}
    }
    
    with patch.object(product_agent.config_loader, 'get_repo_path', return_value='/fake/path'):
        with patch.object(product_agent, 'ensure_project_questionnaire', return_value=questionnaire):
            with patch.object(product_agent.config_loader, '_flatten_questionnaire_intent') as mock_flatten:
                mock_flatten.return_value = {"locked": True}
                
                # Should raise ValueError before trying to use LLM
                with pytest.raises(ValueError, match="intent is locked"):
                    product_agent.create_feature_contract_from_idea(
                        project_id="test-project",
                        idea="Add a feature"
                    )


def test_confidence_below_threshold_prevents_contract_creation():
    """Test that confidence below threshold prevents contract creation."""
    registry = ProjectRegistry()
    # Create ProductAgent without LLM client to avoid API calls
    product_agent = ProductAgent(project_registry=registry, llm_client=None)
    
    # Mock questionnaire with low confidence
    questionnaire = {
        "project_meta": {
            "confidence": 0.5,
            "min_confidence_required": 0.75
        },
        "project_type": {"value": "demo"},
        "intent": {"locked": False}
    }
    
    with patch.object(product_agent.config_loader, 'get_repo_path', return_value='/fake/path'):
        with patch.object(product_agent, 'ensure_project_questionnaire', return_value=questionnaire):
            with patch.object(product_agent.config_loader, '_flatten_questionnaire_intent') as mock_flatten:
                mock_flatten.return_value = {
                    "locked": False,
                    "confidence": 0.5,
                    "min_confidence_required": 0.75
                }
                
                # Should raise ValueError before trying to use LLM
                with pytest.raises(ValueError, match="confidence.*below required threshold"):
                    product_agent.create_feature_contract_from_idea(
                        project_id="test-project",
                        idea="Add a feature"
                    )


def test_intent_snapshot_creation():
    """Test that intent snapshot is created correctly."""
    from agents.product.product_agent import ProductAgent
    
    product_agent = ProductAgent()
    
    intent = {
        "project_type": "demo",
        "ui": "none",
        "backend": "fastapi",
        "auth_enabled": False,
        "persistence": "none",
        "complexity": "toy",
        "monitoring": True,
        "tests_required": True
    }
    
    snapshot = product_agent._create_intent_snapshot(intent)
    
    # Check snapshot contains all fields
    assert snapshot["project_type"] == "demo"
    assert snapshot["ui"] == "none"
    assert snapshot["backend"] == "fastapi"
    assert snapshot["auth_enabled"] is False
    
    # Check hash is present
    assert "hash" in snapshot
    assert len(snapshot["hash"]) == 12  # First 12 chars of SHA256
    
    # Check hash is deterministic
    snapshot2 = product_agent._create_intent_snapshot(intent)
    assert snapshot2["hash"] == snapshot["hash"]


def test_intent_snapshot_yaml_formatting():
    """Test that intent snapshot is formatted correctly as YAML."""
    from agents.product.product_agent import ProductAgent
    
    product_agent = ProductAgent()
    
    snapshot = {
        "project_type": "demo",
        "ui": "none",
        "backend": "fastapi",
        "auth_enabled": False,
        "out_of_scope": ["payments", "notifications"],
        "hash": "abc123"
    }
    
    yaml_str = product_agent._format_snapshot_yaml(snapshot)
    
    # Check hash is not included
    assert "hash" not in yaml_str
    
    # Check key fields are present
    assert "project_type: demo" in yaml_str
    assert "backend: fastapi" in yaml_str
    assert "auth_enabled: false" in yaml_str
    
    # Check list formatting
    assert "out_of_scope:" in yaml_str
    assert "- payments" in yaml_str
    assert "- notifications" in yaml_str

