"""Unit tests for ConfigLoader questionnaire intent flattening."""

import pytest
from autopilot_core.config.loader import ConfigLoader
from autopilot_core.config.project_registry import ProjectRegistry


def test_flatten_questionnaire_intent_empty():
    """Test flattening empty questionnaire returns empty dict."""
    loader = ConfigLoader()
    result = loader._flatten_questionnaire_intent({})
    assert result == {}


def test_flatten_questionnaire_intent_example_project():
    """Test flattening example-project questionnaire."""
    loader = ConfigLoader()
    
    questionnaire = {
        "project_meta": {
            "name": "example-project",
            "description": "Internal golden-path FastAPI demo"
        },
        "project_type": {
            "value": "demo"
        },
        "architecture": {
            "ui": {
                "value": "none"
            },
            "backend": {
                "value": "fastapi"
            }
        },
        "ui_details": {
            "framework": {
                "value": "none"
            },
            "pages": {
                "value": []
            }
        },
        "auth": {
            "enabled": {
                "value": False
            },
            "providers": {
                "value": []
            }
        },
        "data": {
            "persistence": {
                "value": "none"
            },
            "multi_user": {
                "value": False
            }
        },
        "constraints": {
            "complexity": {
                "value": "toy"
            },
            "monitoring": {
                "value": True
            },
            "tests_required": {
                "value": True
            }
        }
    }
    
    result = loader._flatten_questionnaire_intent(questionnaire)
    
    assert result["project_type"] == "demo"
    assert result["ui"] == "none"
    assert result["backend"] == "fastapi"
    assert result["ui_framework"] == "none"
    assert result["ui_pages"] == []
    assert result["auth_enabled"] is False
    assert result["auth_providers"] == []
    assert result["persistence"] == "none"
    assert result["multi_user"] is False
    assert result["complexity"] == "toy"
    assert result["monitoring"] is True
    assert result["tests_required"] is True


def test_flatten_questionnaire_intent_web_app():
    """Test flattening questionnaire for a web app with auth."""
    loader = ConfigLoader()
    
    questionnaire = {
        "project_type": {"value": "production"},
        "architecture": {
            "ui": {"value": "web"},
            "backend": {"value": "fastapi"}
        },
        "ui_details": {
            "framework": {"value": "nextjs"},
            "pages": {"value": ["landing", "dashboard"]}
        },
        "auth": {
            "enabled": {"value": True},
            "providers": {"value": ["email_password", "oauth_google"]}
        },
        "data": {
            "persistence": {"value": "postgres"},
            "multi_user": {"value": True}
        },
        "constraints": {
            "complexity": {"value": "realistic"},
            "monitoring": {"value": True},
            "tests_required": {"value": True}
        }
    }
    
    result = loader._flatten_questionnaire_intent(questionnaire)
    
    assert result["project_type"] == "production"
    assert result["ui"] == "web"
    assert result["backend"] == "fastapi"
    assert result["ui_framework"] == "nextjs"
    assert result["ui_pages"] == ["landing", "dashboard"]
    assert result["auth_enabled"] is True
    assert result["auth_providers"] == ["email_password", "oauth_google"]
    assert result["persistence"] == "postgres"
    assert result["multi_user"] is True
    assert result["complexity"] == "realistic"
    assert result["monitoring"] is True
    assert result["tests_required"] is True


def test_flatten_questionnaire_intent_partial():
    """Test flattening questionnaire with missing fields."""
    loader = ConfigLoader()
    
    questionnaire = {
        "project_type": {"value": "demo"},
        "architecture": {
            "backend": {"value": "fastapi"}
        }
    }
    
    result = loader._flatten_questionnaire_intent(questionnaire)
    
    assert result["project_type"] == "demo"
    assert result["backend"] == "fastapi"
    # Missing fields should be None or default
    assert result.get("ui") is None
    assert result.get("auth_enabled") is None


def test_flatten_questionnaire_intent_with_refinements():
    """Test flattening questionnaire with locked, confidence, and out_of_scope."""
    loader = ConfigLoader()
    
    questionnaire = {
        "project_meta": {
            "confidence": 0.85,
            "min_confidence_required": 0.75
        },
        "project_type": {"value": "demo"},
        "architecture": {
            "backend": {"value": "fastapi"}
        },
        "constraints": {
            "out_of_scope": {"value": ["payments", "notifications", "admin panel"]}
        },
        "intent": {
            "locked": True
        }
    }
    
    result = loader._flatten_questionnaire_intent(questionnaire)
    
    assert result["locked"] is True
    assert result["confidence"] == 0.85
    assert result["min_confidence_required"] == 0.75
    assert result["out_of_scope"] == ["payments", "notifications", "admin panel"]


def test_flatten_questionnaire_intent_locked_default():
    """Test that locked defaults to False if not specified."""
    loader = ConfigLoader()
    
    questionnaire = {
        "project_type": {"value": "demo"}
    }
    
    result = loader._flatten_questionnaire_intent(questionnaire)
    
    assert result["locked"] is False  # Default value

