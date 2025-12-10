"""Bugfix agent for generating bugfix patches and regression tests."""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from autopilot_core.clients.llm_client import LLMClient
from agents.bugfix.prompts import BUGFIX_SYSTEM_PROMPT, build_bugfix_prompt


@dataclass
class Patch:
    """Represents a bugfix patch."""
    file_path: str
    unified_diff: str
    notes: str = ""


@dataclass
class BugfixRequest:
    """Request for bugfix analysis."""
    command: str
    exit_code: int
    stdout: str
    stderr: str
    changed_files: Optional[List[str]] = None
    project_config: Optional[Dict[str, Any]] = None


@dataclass
class BugfixResponse:
    """Response from bugfix agent."""
    patches: List[Patch]
    retry_command: str
    notes: str
    success: bool = True


class BugfixAgent:
    """Agent that creates scoped bugfix patches and regression tests."""
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        """
        Initialize bugfix agent.
        
        Args:
            llm_client: LLM client for generating fixes (optional)
        """
        self.llm_client = llm_client
        if not self.llm_client:
            try:
                self.llm_client = LLMClient()
            except ValueError:
                # LLM not configured, will raise error when used
                self.llm_client = None
    
    def suggest_fixes(self, request: BugfixRequest) -> BugfixResponse:
        """
        Analyze test failure and suggest fixes as patches.
        
        Args:
            request: Bugfix request with test failure details
            
        Returns:
            BugfixResponse: Patches, retry command, and notes
            
        Raises:
            ValueError: If LLM client is not available
        """
        if not self.llm_client:
            raise ValueError("LLM client required for bugfix suggestions")
        
        prompt = build_bugfix_prompt(
            command=request.command,
            exit_code=request.exit_code,
            stdout=request.stdout,
            stderr=request.stderr,
            changed_files=request.changed_files,
            project_config=request.project_config
        )
        
        try:
            response_text = self.llm_client.generate(
                prompt=prompt,
                system_prompt=BUGFIX_SYSTEM_PROMPT,
                temperature=0.2,  # Lower temperature for more deterministic fixes
                max_tokens=2000
            )
            
            # Parse response
            patches = self._parse_patches(response_text)
            retry_command = self._extract_retry_command(response_text)
            notes = self._extract_notes(response_text)
            
            return BugfixResponse(
                patches=patches,
                retry_command=retry_command or request.command,
                notes=notes,
                success=True
            )
        except Exception as e:
            return BugfixResponse(
                patches=[],
                retry_command=request.command,
                notes=f"Error generating fix: {str(e)}",
                success=False
            )
    
    def _parse_patches(self, response_text: str) -> List[Patch]:
        """Parse patches from LLM response."""
        patches = []
        
        # Look for PATCH: section
        if "PATCH:" in response_text:
            patch_section = response_text.split("PATCH:")[1]
            if "RETRY_COMMAND:" in patch_section:
                patch_section = patch_section.split("RETRY_COMMAND:")[0]
            elif "NOTES:" in patch_section:
                patch_section = patch_section.split("NOTES:")[0]
            
            # Extract unified diff
            lines = patch_section.strip().split("\n")
            current_file = None
            current_diff = []
            
            for line in lines:
                if line.startswith("---") or line.startswith("+++"):
                    # File header
                    if line.startswith("---"):
                        if current_file and current_diff:
                            patches.append(Patch(
                                file_path=current_file,
                                unified_diff="\n".join(current_diff)
                            ))
                        current_file = line.replace("---", "").strip().lstrip("a/").lstrip("b/")
                        current_diff = [line]
                    else:
                        current_diff.append(line)
                elif line.startswith("@@"):
                    # Hunk header
                    current_diff.append(line)
                elif current_file:
                    current_diff.append(line)
            
            if current_file and current_diff:
                patches.append(Patch(
                    file_path=current_file,
                    unified_diff="\n".join(current_diff)
                ))
        
        return patches
    
    def _extract_retry_command(self, response_text: str) -> Optional[str]:
        """Extract retry command from response."""
        if "RETRY_COMMAND:" in response_text:
            retry_section = response_text.split("RETRY_COMMAND:")[1]
            if "NOTES:" in retry_section:
                retry_section = retry_section.split("NOTES:")[0]
            return retry_section.strip()
        return None
    
    def _extract_notes(self, response_text: str) -> str:
        """Extract notes from response."""
        if "NOTES:" in response_text:
            notes_section = response_text.split("NOTES:")[1]
            return notes_section.strip()
        return ""
    
    def analyze_error(self, error_info: dict, logs: list = None):
        """
        Analyze error to identify root cause.
        
        Args:
            error_info: Error information (stack trace, message, etc.)
            logs: Relevant log entries
            
        Returns:
            dict: Analysis result with root cause
        """
        # Legacy method - delegate to suggest_fixes
        request = BugfixRequest(
            command=error_info.get("command", ""),
            exit_code=error_info.get("exit_code", 1),
            stdout=error_info.get("stdout", ""),
            stderr=error_info.get("stderr", ""),
            changed_files=error_info.get("changed_files"),
            project_config=error_info.get("project_config")
        )
        response = self.suggest_fixes(request)
        return {
            "root_cause": response.notes,
            "patches": [{"file": p.file_path, "diff": p.unified_diff} for p in response.patches],
            "retry_command": response.retry_command
        }
    
    def generate_bugfix_patch(self, error_analysis: dict, project_config: dict):
        """
        Generate a scoped bugfix patch.
        
        Args:
            error_analysis: Error analysis result
            project_config: Project configuration
            
        Returns:
            dict: Bugfix patch files and changes
        """
        # Legacy method - use error_analysis to build request
        request = BugfixRequest(
            command=error_analysis.get("command", ""),
            exit_code=error_analysis.get("exit_code", 1),
            stdout=error_analysis.get("stdout", ""),
            stderr=error_analysis.get("stderr", ""),
            changed_files=error_analysis.get("changed_files"),
            project_config=project_config
        )
        response = self.suggest_fixes(request)
        return {
            "patches": [{"file": p.file_path, "diff": p.unified_diff} for p in response.patches],
            "retry_command": response.retry_command
        }
    
    def generate_regression_test(self, error_analysis: dict, bugfix_patch: dict, project_config: dict):
        """
        Generate regression test to prevent recurrence.
        
        Args:
            error_analysis: Error analysis result
            bugfix_patch: Generated bugfix patch
            project_config: Project configuration
            
        Returns:
            dict: Regression test files
        """
        # Stub for now - can be enhanced later
        return {"test_files": []}

