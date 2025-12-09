"""Product agent for taking ideas and creating design contracts."""

import os
import re
from typing import Dict


class ProductAgent:
    """Agent that works with humans to define features and create design contracts."""
    
    def __init__(self, llm_client=None):
        """
        Initialize product agent.
        
        Args:
            llm_client: LLM client for generating content (not used in v0)
        """
        pass
    
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
        
        # Build full path
        base_path = os.path.join("configs", "examples", project_id, ".sanjaya", "design-contracts")
        os.makedirs(base_path, exist_ok=True)
        
        full_path = os.path.join(base_path, filename)
        
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
        
        # Write file
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        # Return contract_path relative to .sanjaya
        contract_path = f"design-contracts/{filename}"
        
        return {
            "project_id": project_id,
            "contract_path": contract_path
        }
    
    def clarify_requirements(self, idea: str, context: dict = None):
        """
        Clarify requirements through dialogue with human.
        
        Args:
            idea: Initial feature idea
            context: Additional context about the project
            
        Returns:
            dict: Clarified requirements
        """
        pass
    
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

