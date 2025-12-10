"""Product agent for taking ideas and creating design contracts."""

import os
import re
import yaml
import hashlib
import json
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime
from autopilot_core.config.loader import ConfigLoader
from autopilot_core.config.project_registry import ProjectRegistry
from autopilot_core.clients.repo_client import RepoClient
from autopilot_core.clients.llm_client import LLMClient, LLMProvider
from agents.product.prompts import FEATURE_DESIGN_SYSTEM_PROMPT, build_feature_design_prompt


class ProductAgent:
    """Agent that works with humans to define features and create design contracts."""
    
    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        project_registry: Optional[ProjectRegistry] = None,
        llm_provider: str = "openai"
    ):
        """
        Initialize product agent.
        
        Args:
            llm_client: LLM client for generating content (optional, will create if not provided)
            project_registry: Project registry instance (optional)
            llm_provider: LLM provider to use ("openai" or "anthropic")
        """
        self.project_registry = project_registry or ProjectRegistry()
        self.config_loader = ConfigLoader(project_registry=self.project_registry)
        self.repo_client = RepoClient()
        
        # Initialize LLM client if not provided
        if llm_client:
            self.llm_client = llm_client
        else:
            try:
                self.llm_client = LLMClient(provider=llm_provider)
            except (ValueError, ImportError) as e:
                # If LLM is not configured, we'll still work but LLM features won't be available
                print(f"Warning: LLM client not available: {e}")
                self.llm_client = None
    
    def _get_questionnaire_path(self, project_id: str) -> Optional[Path]:
        """
        Get the path to questionnaire.yaml for a project.
        
        Args:
            project_id: Project identifier
            
        Returns:
            Path to questionnaire.yaml, or None if project not found
        """
        repo_path = self.config_loader.get_repo_path(project_id)
        if not repo_path:
            return None
        return Path(repo_path) / ".sanjaya" / "questionnaire.yaml"
    
    def ensure_project_questionnaire(self, project_id: str) -> Dict[str, Any]:
        """
        Ensure a questionnaire.yaml exists for the project.
        If missing, create it with sensible defaults derived from template.
        
        Args:
            project_id: Project identifier
            
        Returns:
            dict: Loaded questionnaire dict
        """
        q_path = self._get_questionnaire_path(project_id)
        if not q_path:
            raise ValueError(f"Project '{project_id}' not found. Cannot create questionnaire.")
        
        if not q_path.exists():
            # Load template
            template_path = Path("docs/project_questionnaire_template.yaml")
            if not template_path.exists():
                # If template doesn't exist, create minimal defaults
                q_data = {
                    "project_meta": {
                        "name": project_id,
                        "description": f"Project {project_id}"
                    },
                    "project_type": {"value": "demo"},
                    "architecture": {
                        "ui": {"value": "none"},
                        "backend": {"value": "fastapi"}
                    },
                    "ui_details": {
                        "framework": {"value": "none"},
                        "pages": {"value": []}
                    },
                    "auth": {
                        "enabled": {"value": False},
                        "providers": {"value": []}
                    },
                    "data": {
                        "persistence": {"value": "none"},
                        "multi_user": {"value": False}
                    },
                    "constraints": {
                        "complexity": {"value": "toy"},
                        "monitoring": {"value": True},
                        "tests_required": {"value": True}
                    }
                }
            else:
                with template_path.open("r", encoding="utf-8") as f:
                    q_data = yaml.safe_load(f) or {}
                
                # Adjust project_meta based on project_id
                if "project_meta" in q_data:
                    q_data["project_meta"]["name"] = project_id
            
            # Ensure directory exists
            q_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write questionnaire
            with q_path.open("w", encoding="utf-8") as f:
                yaml.safe_dump(q_data, f, sort_keys=False, default_flow_style=False)
            
            return q_data
        
        # Load existing questionnaire
        with q_path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    
    def _slugify(self, text: str) -> str:
        """
        Convert text to a filesystem-safe slug.
        
        Args:
            text: Text to slugify
            
        Returns:
            str: Slugified text (lowercase, hyphens, no spaces)
        """
        # Convert to lowercase
        text = text.lower()
        # Replace spaces and underscores with hyphens
        text = re.sub(r'[\s_]+', '-', text)
        # Remove all non-alphanumeric characters except hyphens
        text = re.sub(r'[^a-z0-9-]', '', text)
        # Remove multiple consecutive hyphens
        text = re.sub(r'-+', '-', text)
        # Remove leading/trailing hyphens
        text = text.strip('-')
        return text
    
    def create_feature_contract(
        self,
        project_id: str,
        feature_name: str,
        summary: str,
        problem: str,
        user_story: str,
        notes: str = ""
    ) -> Dict[str, str]:
        """
        Create a feature design contract markdown file.
        
        Works with both GitHub repos and local paths.
        For GitHub repos, writes to cached clone and commits changes.
        
        Args:
            project_id: ID of the project
            feature_name: Name of the feature
            summary: Summary of the feature
            problem: Problem statement
            user_story: User story
            notes: Additional notes (optional)
            
        Returns:
            dict: Contains project_id and contract_path (relative to .sanjaya)
        """
        # Slugify feature name for filename
        slug = self._slugify(feature_name)
        filename = f"{slug}.md"
        contract_path = f"design-contracts/{filename}"
        
        # Get repo path (GitHub cache or local)
        repo_path = self.config_loader.get_repo_path(project_id)
        
        if not repo_path:
            raise ValueError(
                f"Project '{project_id}' not found. "
                f"Please register the project first or ensure it exists locally."
            )
        
        # Set up repo client
        self.repo_client.set_repo_path(repo_path)
        
        # Generate markdown content
        markdown_content = f"""# Feature: {feature_name}

## 1. Summary

{summary}

## 2. Problem Statement

{problem}

## 3. User Story

{user_story}

## 4. Scope

- Initial, simple lemonade-stand planner scope.

- This is a demo feature for Sanjaya.

## 5. Business Rules

- Add business rules later.

## 6. Logging & Monitoring

- Log all errors with a structured JSON log entry.

- Example event name: BREAK_EVEN_CALC_FAILED.

## 7. Acceptance Criteria

- [ ] Endpoint returns profit, revenue, cost, and break-even.

- [ ] Handles normal positive-margin cases.

- [ ] Handles price_per_cup <= cost_per_cup gracefully.

## 8. Notes

{notes}
"""
        
        # Write file to repo
        file_path = os.path.join(".sanjaya", contract_path)
        self.repo_client.write_file(file_path, markdown_content)
        
        return {
            "project_id": project_id,
            "contract_path": contract_path
        }
    
    def create_feature_contract_from_idea(
        self,
        project_id: str,
        idea: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Create a comprehensive feature design contract from a simple idea using LLM.
        
        Takes a simple feature idea and uses LLM to generate a full design contract
        with API design, data models, logging, monitoring, tests, and all sections.
        
        Args:
            project_id: ID of the project
            idea: Simple feature idea description
            context: Additional context (optional)
            
        Returns:
            dict: Contains project_id and contract_path (relative to .sanjaya)
            
        Raises:
            ValueError: If LLM client is not available or project not found
        """
        if not self.llm_client:
            raise ValueError(
                "LLM client not available. "
                "Set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable, "
                "or pass an LLMClient instance to ProductAgent."
            )
        
        # Get repo path
        repo_path = self.config_loader.get_repo_path(project_id)
        if not repo_path:
            raise ValueError(
                f"Project '{project_id}' not found. "
                f"Please register the project first or ensure it exists locally."
            )
        
        # Ensure questionnaire exists and load it
        questionnaire = self.ensure_project_questionnaire(project_id)
        intent_flat = self.config_loader._flatten_questionnaire_intent(questionnaire)
        
        # Check if intent is locked
        if intent_flat.get("locked", False):
            raise ValueError(
                f"Project '{project_id}' intent is locked. "
                "ProductAgent cannot suggest changes or re-interpret architecture. "
                "Unlock the intent in questionnaire.yaml to proceed."
            )
        
        # Check confidence threshold
        confidence = intent_flat.get("confidence")
        min_confidence = intent_flat.get("min_confidence_required")
        if confidence is not None and min_confidence is not None:
            if confidence < min_confidence:
                # ProductAgent may ask exactly ONE question if below threshold
                # For now, we'll raise an error - in future, this could trigger a single clarification
                raise ValueError(
                    f"Project '{project_id}' confidence ({confidence}) is below required threshold ({min_confidence}). "
                    "Please update questionnaire.yaml to increase confidence or lower the threshold."
                )
        
        # Load project config for context
        try:
            project_config = self.config_loader.load_project_config(project_id)
        except FileNotFoundError:
            project_config = {}
        
        # Extract tech stack and conventions from config
        tech_stack = project_config.get("tech_stack", "Not specified")
        conventions = project_config.get("conventions", "Standard conventions")
        
        # Build context dict
        project_context = context or {}
        project_context.update({
            "project_id": project_id,
            "project_name": project_config.get("project_name", project_id),
            "intent": intent_flat  # Include questionnaire intent
        })
        
        # Build prompt with intent
        user_prompt = build_feature_design_prompt(
            idea=idea,
            project_context=project_context,
            tech_stack=str(tech_stack),
            conventions=str(conventions),
            intent=intent_flat
        )
        
        # Generate design contract using LLM
        design_content = self.llm_client.generate(
            prompt=user_prompt,
            system_prompt=FEATURE_DESIGN_SYSTEM_PROMPT,
            temperature=0.7,
            max_tokens=4000
        )
        
        # Extract feature name from idea (first few words)
        feature_name = idea.split('.')[0].strip()[:50]  # Use first sentence, max 50 chars
        if not feature_name:
            feature_name = "new-feature"
        
        # Slugify feature name for filename
        slug = self._slugify(feature_name)
        filename = f"{slug}.md"
        contract_path = f"design-contracts/{filename}"
        
        # Build Project Intent section from questionnaire
        intent_section = self._build_intent_section(intent_flat)
        
        # Create intent snapshot for immutability
        intent_snapshot = self._create_intent_snapshot(intent_flat)
        
        # Add metadata header to design contract
        date_str = datetime.now().strftime("%Y-%m-%d")
        full_design_content = f"""# Feature Design Contract

**Feature Name**: {feature_name}

**Date**: {date_str}

**Author**: Product Agent (LLM-Powered)

**Status**: Draft

---

## Project Intent

{intent_section}

---

## Project Intent Snapshot

This snapshot captures the project intent at the time of contract creation. 
Changes to questionnaire.yaml will not affect this contract.

```yaml
project_intent_snapshot:
{self._format_snapshot_yaml(intent_snapshot)}
```

**Snapshot Hash**: `{intent_snapshot['hash']}`

---

{design_content}
"""
        
        # Set up repo client and write file
        self.repo_client.set_repo_path(repo_path)
        file_path = os.path.join(".sanjaya", contract_path)
        self.repo_client.write_file(file_path, full_design_content)
        
        return {
            "project_id": project_id,
            "contract_path": contract_path
        }
    
    def _create_intent_snapshot(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create an immutable snapshot of project intent for design contracts.
        
        Args:
            intent: Flattened intent dict from questionnaire
            
        Returns:
            dict: Intent snapshot with hash for verification
        """
        # Create a clean snapshot (exclude None values and hash itself)
        snapshot = {
            k: v for k, v in intent.items() 
            if v is not None and k != "hash"
        }
        
        # Generate hash for verification
        snapshot_str = json.dumps(snapshot, sort_keys=True)
        snapshot_hash = hashlib.sha256(snapshot_str.encode()).hexdigest()[:12]
        
        snapshot["hash"] = snapshot_hash
        return snapshot
    
    def _format_snapshot_yaml(self, snapshot: Dict[str, Any]) -> str:
        """
        Format intent snapshot as YAML for inclusion in design contract.
        
        Args:
            snapshot: Intent snapshot dict
            
        Returns:
            str: YAML-formatted string (indented)
        """
        lines = []
        for key, value in sorted(snapshot.items()):
            if key == "hash":
                continue  # Hash is shown separately
            if isinstance(value, list):
                if value:
                    lines.append(f"  {key}:")
                    for item in value:
                        lines.append(f"    - {item}")
                else:
                    lines.append(f"  {key}: []")
            elif isinstance(value, bool):
                lines.append(f"  {key}: {str(value).lower()}")
            else:
                lines.append(f"  {key}: {value}")
        return "\n".join(lines)
    
    def _build_intent_section(self, intent: Dict[str, Any]) -> str:
        """
        Build a Project Intent section from flattened intent dict.
        
        Args:
            intent: Flattened intent dict from questionnaire
            
        Returns:
            str: Markdown formatted intent section
        """
        if not intent:
            return "Project intent not specified."
        
        lines = []
        
        if intent.get("project_type"):
            lines.append(f"- **Project type**: {intent['project_type']}")
        
        if intent.get("ui"):
            ui_framework = intent.get("ui_framework", "none")
            if ui_framework != "none":
                lines.append(f"- **UI**: {intent['ui']} ({ui_framework})")
            else:
                lines.append(f"- **UI**: {intent['ui']}")
        
        if intent.get("backend"):
            lines.append(f"- **Backend**: {intent['backend']}")
        
        if intent.get("auth_enabled") is not None:
            auth_status = "enabled" if intent.get("auth_enabled") else "disabled"
            lines.append(f"- **Auth**: {auth_status}")
            if intent.get("auth_enabled") and intent.get("auth_providers"):
                lines.append(f"  - Providers: {', '.join(intent['auth_providers'])}")
        
        if intent.get("persistence"):
            lines.append(f"- **Persistence**: {intent['persistence']}")
        
        if intent.get("multi_user") is not None:
            lines.append(f"- **Multi-user**: {intent['multi_user']}")
        
        if intent.get("complexity"):
            lines.append(f"- **Complexity**: {intent['complexity']}")
        
        if intent.get("monitoring") is not None:
            lines.append(f"- **Monitoring**: {'enabled' if intent['monitoring'] else 'disabled'}")
        
        if intent.get("tests_required") is not None:
            lines.append(f"- **Tests required**: {intent['tests_required']}")
        
        if intent.get("out_of_scope"):
            out_of_scope = intent["out_of_scope"]
            if out_of_scope:
                lines.append(f"- **Out of scope**: {', '.join(out_of_scope)}")
        
        if intent.get("locked") is not None:
            locked_status = "locked" if intent["locked"] else "unlocked"
            lines.append(f"- **Intent locked**: {locked_status}")
        
        return "\n".join(lines) if lines else "Project intent not specified."
    
    def clarify_requirements(self, idea: str, context: dict = None):
        """
        Clarify requirements through dialogue with human using LLM.
        
        Args:
            idea: Initial feature idea
            context: Additional context about the project
            
        Returns:
            dict: Clarified requirements
        """
        if not self.llm_client:
            raise ValueError("LLM client not available for requirement clarification.")
        
        clarification_prompt = f"""Given this feature idea: "{idea}"

Please ask clarifying questions to better understand:
1. The target users
2. The core problem being solved
3. Success criteria
4. Any constraints or requirements

Generate 3-5 clarifying questions that would help refine this feature idea."""
        
        questions = self.llm_client.generate(
            prompt=clarification_prompt,
            system_prompt="You are a product manager helping to clarify feature requirements.",
            temperature=0.7
        )
        
        return {
            "original_idea": idea,
            "clarifying_questions": questions,
            "context": context or {}
        }
    
    def create_design_contract(self, requirements: dict, template_path: str = None):
        """
        Create a design contract from requirements.
        
        Args:
            requirements: Clarified requirements
            template_path: Path to design contract template
            
        Returns:
            str: Path to created design contract file
        """
        pass
    
    def validate_design_contract(self, contract_path: str):
        """
        Validate design contract completeness.
        
        Args:
            contract_path: Path to design contract
            
        Returns:
            tuple: (is_valid, issues)
        """
        pass

