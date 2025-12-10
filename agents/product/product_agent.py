"""Product agent for taking ideas and creating design contracts."""

import os
import re
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
            "project_name": project_config.get("project_name", project_id)
        })
        
        # Build prompt
        user_prompt = build_feature_design_prompt(
            idea=idea,
            project_context=project_context,
            tech_stack=str(tech_stack),
            conventions=str(conventions)
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
        
        # Add metadata header to design contract
        date_str = datetime.now().strftime("%Y-%m-%d")
        full_design_content = f"""# Feature Design Contract

**Feature Name**: {feature_name}

**Date**: {date_str}

**Author**: Product Agent (LLM-Powered)

**Status**: Draft

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

