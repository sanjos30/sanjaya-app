"""Governance agent for enforcing safety rules and compliance."""

import fnmatch
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
from agents.governance.prompts import (
    FORBIDDEN_PATHS_DEFAULT,
    REQUIRE_TESTS_FOR_CODE_PATTERNS,
    ALLOWED_DEPENDENCIES_DEFAULT,
)


@dataclass
class GovernanceRuleViolation:
    """Represents a governance rule violation."""
    rule_name: str
    severity: str  # "error", "warning"
    message: str
    file_path: Optional[str] = None


@dataclass
class GovernanceResult:
    """Result of governance evaluation."""
    ok: bool
    violations: List[GovernanceRuleViolation]
    summary: str = ""


class GovernanceAgent:
    """Agent that enforces safety rules and validates compliance."""
    
    def __init__(self):
        """Initialize governance agent."""
        pass
    
    def evaluate(self, diff: str, project_config: Dict[str, Any]) -> GovernanceResult:
        """
        Evaluate a diff against governance rules.
        
        Args:
            diff: Git diff (unified diff format)
            project_config: Project configuration with governance rules
            
        Returns:
            GovernanceResult: Evaluation result with violations
        """
        violations: List[GovernanceRuleViolation] = []
        
        # Get governance config
        governance_config = project_config.get("governance", {}) if isinstance(project_config, dict) else {}
        
        # Extract changed files from diff
        changed_files = self._extract_changed_files(diff)
        
        # Rule 1: Check forbidden paths
        forbidden_paths = governance_config.get("forbidden_paths", FORBIDDEN_PATHS_DEFAULT)
        for file_path in changed_files:
            if self._matches_patterns(file_path, forbidden_paths):
                violations.append(GovernanceRuleViolation(
                    rule_name="forbidden_paths",
                    severity="error",
                    message=f"File '{file_path}' matches forbidden path pattern",
                    file_path=file_path
                ))
        
        # Rule 2: Require tests for code changes
        require_tests = governance_config.get("require_tests_for_code", True)
        if require_tests:
            language = str(project_config.get("language", "python")).lower()
            code_patterns = REQUIRE_TESTS_FOR_CODE_PATTERNS.get(language, [])
            
            code_files = [f for f in changed_files if self._matches_patterns(f, code_patterns)]
            test_files = [f for f in changed_files if self._is_test_file(f, language)]
            
            if code_files and not test_files:
                violations.append(GovernanceRuleViolation(
                    rule_name="require_tests_for_code",
                    severity="warning",
                    message=f"Code changes detected in {len(code_files)} file(s) but no test files found",
                    file_path=None
                ))
        
        # Rule 3: Check allowed dependencies (if configured)
        allowed_deps = governance_config.get("allowed_dependencies", {})
        if allowed_deps:
            language = str(project_config.get("language", "python")).lower()
            deps_list = allowed_deps.get(language, [])
            
            if deps_list:  # Empty list means no restrictions
                # Check dependency manifest files
                dep_manifest_files = {
                    "python": ["requirements.txt", "pyproject.toml", "setup.py"],
                    "javascript": ["package.json"],
                    "php": ["composer.json"],
                }.get(language, [])
                
                for file_path in changed_files:
                    if any(file_path.endswith(manifest) for manifest in dep_manifest_files):
                        # Parse diff to find added dependencies
                        added_deps = self._extract_added_dependencies(diff, file_path, language)
                        for dep in added_deps:
                            if not self._matches_patterns(dep, deps_list):
                                violations.append(GovernanceRuleViolation(
                                    rule_name="allowed_dependencies",
                                    severity="error",
                                    message=f"Dependency '{dep}' is not in allowed list",
                                    file_path=file_path
                                ))
        
        ok = len([v for v in violations if v.severity == "error"]) == 0
        summary = f"Found {len(violations)} violation(s): {len([v for v in violations if v.severity == 'error'])} error(s), {len([v for v in violations if v.severity == 'warning'])} warning(s)"
        
        return GovernanceResult(
            ok=ok,
            violations=violations,
            summary=summary
        )
    
    def _extract_changed_files(self, diff: str) -> List[str]:
        """Extract list of changed files from unified diff."""
        files = []
        for line in diff.split("\n"):
            if line.startswith("---") or line.startswith("+++"):
                file_path = line.replace("---", "").replace("+++", "").strip()
                # Remove a/ or b/ prefix
                file_path = file_path.lstrip("a/").lstrip("b/")
                if file_path and file_path != "/dev/null" and file_path not in files:
                    files.append(file_path)
        return files
    
    def _matches_patterns(self, file_path: str, patterns: List[str]) -> bool:
        """Check if file path matches any of the glob patterns."""
        for pattern in patterns:
            if fnmatch.fnmatch(file_path, pattern):
                return True
        return False
    
    def _is_test_file(self, file_path: str, language: str) -> bool:
        """Check if file is a test file."""
        test_patterns = {
            "python": ["**/test_*.py", "**/*_test.py", "**/tests/**/*.py"],
            "javascript": ["**/*.test.js", "**/*.test.ts", "**/*.spec.js", "**/*.spec.ts", "**/__tests__/**"],
            "php": ["**/*Test.php", "**/tests/**/*.php"],
        }
        patterns = test_patterns.get(language.lower(), [])
        return self._matches_patterns(file_path, patterns)
    
    def _extract_added_dependencies(self, diff: str, file_path: str, language: str) -> List[str]:
        """Extract added dependencies from diff."""
        deps = []
        in_file = False
        in_added_section = False
        
        for line in diff.split("\n"):
            if line.startswith("+++") and file_path in line:
                in_file = True
                continue
            
            if in_file:
                if line.startswith("@@"):
                    in_added_section = True
                    continue
                
                if line.startswith("---") or line.startswith("+++"):
                    break
                
                if in_added_section and line.startswith("+"):
                    dep_line = line[1:].strip()
                    # Parse based on language
                    if language == "python":
                        # requirements.txt: package==version or package>=version
                        if "==" in dep_line or ">=" in dep_line or ">" in dep_line:
                            dep = dep_line.split("==")[0].split(">=")[0].split(">")[0].strip()
                            if dep and not dep.startswith("#"):
                                deps.append(dep)
                    elif language == "javascript":
                        # package.json: "package": "version"
                        if '"' in dep_line and ":" in dep_line:
                            dep = dep_line.split(":")[0].strip().strip('"').strip("'")
                            if dep and not dep.startswith("//"):
                                deps.append(dep)
                    elif language == "php":
                        # composer.json: "package": "version"
                        if '"' in dep_line and ":" in dep_line:
                            dep = dep_line.split(":")[0].strip().strip('"').strip("'")
                            if dep and not dep.startswith("//"):
                                deps.append(dep)
        
        return deps
    
    def validate_safety_rules(self, proposed_changes: dict, project_config: dict):
        """
        Validate proposed changes against safety rules.
        
        Args:
            proposed_changes: Changes to validate
            project_config: Project configuration with safety rules
            
        Returns:
            tuple: (is_safe, violations)
        """
        diff = proposed_changes.get("diff", "")
        result = self.evaluate(diff, project_config)
        return result.ok, result.violations
    
    def ensure_compliance(self, changes: dict, autopilot_config: dict):
        """
        Ensure changes comply with autopilot.yaml configuration.
        
        Args:
            changes: Proposed changes
            autopilot_config: Project autopilot.yaml configuration
            
        Returns:
            tuple: (is_compliant, issues)
        """
        diff = changes.get("diff", "")
        result = self.evaluate(diff, autopilot_config)
        return result.ok, result.violations
    
    def assess_risk(self, changes: dict, project_config: dict):
        """
        Assess risk level of proposed changes.
        
        Args:
            changes: Proposed changes
            project_config: Project configuration
            
        Returns:
            dict: Risk assessment result
        """
        diff = changes.get("diff", "")
        result = self.evaluate(diff, project_config)
        
        error_count = len([v for v in result.violations if v.severity == "error"])
        warning_count = len([v for v in result.violations if v.severity == "warning"])
        
        if error_count > 0:
            risk_level = "high"
        elif warning_count > 0:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return {
            "risk_level": risk_level,
            "violations": result.violations,
            "summary": result.summary
        }
    
    def enforce_guardrails(self, operation: dict, project_config: dict):
        """
        Enforce guardrails and boundaries.
        
        Args:
            operation: Operation to validate
            project_config: Project configuration
            
        Returns:
            tuple: (is_allowed, reason)
        """
        # Basic guardrails check
        if "diff" in operation:
            result = self.evaluate(operation["diff"], project_config)
            if not result.ok:
                return False, result.summary
        return True, "Operation allowed"

