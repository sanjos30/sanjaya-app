import os
from typing import Tuple, Literal, Dict, Any, Optional, List
from datetime import datetime
import subprocess
import time
from enum import Enum

from autopilot_core.config.loader import ConfigLoader
from autopilot_core.config.project_registry import ProjectRegistry
from autopilot_core.clients.repo_client import RepoClient
from agents.codegen.codegen_agent import CodegenAgent
from agents.bugfix.bugfix_agent import BugfixAgent, BugfixRequest
from agents.governance.governance_agent import GovernanceAgent


class WorkflowStatus(str, Enum):
    """Workflow execution status."""
    SUCCESS = "success"
    FAILED_TESTS = "failed_tests"
    FAILED_SMOKE = "failed_smoke"
    FAILED_GOVERNANCE = "failed_governance"
    ERROR = "error"

class OrchestratorAgent:
    """
    OrchestratorAgent coordinates workflows between agents.

    Step 2 Version:
    - Loads project config (from GitHub repo or local path)
    - Validates design contract file exists
    - Returns a structured workflow plan
    """

    def __init__(self, project_registry: ProjectRegistry = None):
        """
        Initialize orchestrator agent.
        
        Args:
            project_registry: Project registry instance (optional)
        """
        self.project_registry = project_registry or ProjectRegistry()
        self.config_loader = ConfigLoader(project_registry=self.project_registry)
        self.repo_client = RepoClient()
        self.codegen_agent = CodegenAgent()
        self.bugfix_agent = BugfixAgent()
        self.governance_agent = GovernanceAgent()

    def run_feature_workflow(
        self,
        project_id: str,
        contract_path: str,
        dry_run: bool = True,
        run_codegen: bool = False,
        run_tests: bool = False,
        create_pr: bool = False,
        branch_name: Optional[str] = None,
        commit_message: Optional[str] = None,
        push_branch: bool = False,
        pr_base: str = "main",
        pr_title: Optional[str] = None,
        pr_body: Optional[str] = None,
        run_smoke: bool = False,
        smoke_timeout: int = 60,
        smoke_health_path: str = "/health",
        run_bugfix: bool = False,
    ) -> Tuple[str, Literal["accepted", "rejected", "error"], str, Dict[str, Any]]:

        workflow_id = self._generate_workflow_id(project_id)

        # 1. Load project config
        try:
            config = self.config_loader.load_project_config(project_id)
        except FileNotFoundError as e:
            return workflow_id, "rejected", "Project config not found", {"error": str(e)}

        # 2. Verify contract file exists
        repo_path = self.config_loader.get_repo_path(project_id)
        if not repo_path:
            return workflow_id, "rejected", "Project repository not found", {
                "project_id": project_id
            }
        
        # Set up repo client
        self.repo_client.set_repo_path(repo_path)
        
        # Check if contract file exists
        full_contract_path = os.path.join(repo_path, ".sanjaya", contract_path)
        if not os.path.exists(full_contract_path):
            return workflow_id, "rejected", "Design contract missing", {
                "expected_path": contract_path,
                "full_path": full_contract_path
            }

        # 3. Workflow response payload
        details: Dict[str, Any] = {
            "project_id": project_id,
            "autopilot_config": config,
            "design_contract": contract_path,
            "repo_path": repo_path,
            "dry_run": dry_run,
            "workflow_steps": [
                "load_project_config",
                "validate_contract_exists",
            ],
        }

        # 4. If dry_run, stop after validation
        if dry_run:
            details["workflow_steps"].extend([
                "prepare_codegen_inputs",
                "invoke_codegen_agent (skipped, dry_run)",
                "run_tests (skipped, dry_run)",
                "prepare_pull_request (skipped, dry_run)"
            ])
            return workflow_id, "accepted", "Feature workflow validated (dry_run)", details

        # 5. Execute codegen if requested
        generated_files = []
        feature_slug = None
        if run_codegen:
            try:
                self.repo_client.set_repo_path(repo_path)
                codegen_result = self.codegen_agent.generate_artifacts(
                    project_id=project_id,
                    repo_path=repo_path,
                    contract_path=contract_path,
                    project_config=config,
                )
                generated_files = codegen_result.get("generated_files", [])
                feature_slug = codegen_result.get("feature_slug")
                details["workflow_steps"].append("invoke_codegen_agent")
                details["generated_files"] = generated_files
                details["feature_slug"] = feature_slug
            except Exception as e:
                return workflow_id, "error", "Codegen failed", {
                    "error": str(e),
                    "contract_path": contract_path
                }
        else:
            details["workflow_steps"].append("invoke_codegen_agent (skipped)")

        # 6. Run tests if requested
        if run_tests:
            test_result = self._run_tests(repo_path, config)
            details["workflow_steps"].append("run_tests")
            details["test_result"] = test_result
            
            # 6a. If tests failed and run_bugfix is True, suggest fixes
            if run_bugfix and test_result.get("status") == "failed":
                bugfix_result = self._run_bugfix(
                    repo_path=repo_path,
                    test_result=test_result,
                    generated_files=generated_files,
                    project_config=config
                )
                details["workflow_steps"].append("run_bugfix")
                details["bugfix_result"] = bugfix_result
        else:
            details["workflow_steps"].append("run_tests (skipped)")

        # 7. Run governance check before PR creation
        governance_result = None
        if create_pr:
            try:
                diff = self.repo_client.get_diff()
                governance_result = self.governance_agent.evaluate(diff, config)
                details["workflow_steps"].append("governance_check")
                details["governance"] = {
                    "ok": governance_result.ok,
                    "violations": [
                        {
                            "rule_name": v.rule_name,
                            "severity": v.severity,
                            "message": v.message,
                            "file_path": v.file_path
                        }
                        for v in governance_result.violations
                    ],
                    "summary": governance_result.summary
                }
            except Exception as e:
                details["governance"] = {"error": str(e)}
        
        # 8. Create PR (real or stub) if requested
        if create_pr:
            pr_info = self._create_pr(
                repo_path=repo_path,
                feature_slug=feature_slug or "feature",
                branch_name=branch_name,
                commit_message=commit_message or f"feat: {feature_slug or contract_path}",
                push_branch=push_branch,
                pr_base=pr_base,
                pr_title=pr_title,
                pr_body=pr_body,
                project_config=config,
            )
            details["workflow_steps"].append("prepare_pull_request")
            details["pr"] = pr_info
        else:
            details["workflow_steps"].append("prepare_pull_request (skipped)")

        # 9. Run smoke if requested
        smoke_result = None
        if run_smoke:
            smoke_result = self._run_smoke(repo_path, config, smoke_timeout)
            details["workflow_steps"].append("run_smoke")
            details["smoke_result"] = smoke_result
        else:
            details["workflow_steps"].append("run_smoke (skipped)")

        # 10. Compute workflow status and add status fields
        test_result_data = details.get("test_result", {})
        tests_passed = test_result_data.get("status") == "passed" if test_result_data else None
        if run_tests and tests_passed is None:
            tests_passed = False  # If tests were run but no result, assume failed
        
        smoke_passed = None
        if run_smoke and smoke_result:
            smoke_passed = smoke_result.get("status") == "passed"
        
        governance_ok = None
        if create_pr and governance_result:
            governance_ok = governance_result.ok
        
        # Determine workflow status
        workflow_status = self._compute_workflow_status(
            tests_passed=tests_passed,
            run_tests=run_tests,
            smoke_passed=smoke_passed,
            run_smoke=run_smoke,
            governance_ok=governance_ok,
            create_pr=create_pr
        )
        
        details["workflow_status"] = workflow_status.value if workflow_status else None
        details["tests_passed"] = tests_passed
        details["smoke_passed"] = smoke_passed
        details["governance_ok"] = governance_ok

        return workflow_id, "accepted", "Feature workflow executed", details

    def _generate_workflow_id(self, project_id: str) -> str:
        ts = datetime.utcnow().isoformat()
        return f"wf-{project_id}-{ts}"

    def _compute_workflow_status(
        self,
        tests_passed: Optional[bool],
        run_tests: bool,
        smoke_passed: Optional[bool],
        run_smoke: bool,
        governance_ok: Optional[bool],
        create_pr: bool
    ) -> WorkflowStatus:
        """
        Compute overall workflow status based on test, smoke, and governance results.
        
        Priority:
        1. If tests failed -> FAILED_TESTS
        2. If smoke failed -> FAILED_SMOKE
        3. If governance failed -> FAILED_GOVERNANCE
        4. Otherwise -> SUCCESS
        """
        if run_tests and tests_passed is False:
            return WorkflowStatus.FAILED_TESTS
        
        if run_smoke and smoke_passed is False:
            return WorkflowStatus.FAILED_SMOKE
        
        if create_pr and governance_ok is False:
            return WorkflowStatus.FAILED_GOVERNANCE
        
        return WorkflowStatus.SUCCESS

    def _run_tests(self, repo_path: str, project_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run basic tests based on project config. Currently supports Python/pytest stub.
        """
        language = str(project_config.get("language", "python")).lower()
        test_cmd = project_config.get("test_command")

        if not test_cmd:
            if language == "python":
                test_cmd = "pytest"
            elif language in ("js", "javascript", "node"):
                test_cmd = "npm test"
            elif language == "php":
                test_cmd = "phpunit"
            else:
                return {"status": "skipped", "reason": "No test_command configured"}

        try:
            result = subprocess.run(
                test_cmd,
                shell=True,
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=120,
            )
            return {
                "status": "passed" if result.returncode == 0 else "failed",
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": test_cmd,
            }
        except Exception as e:
            return {"status": "error", "error": str(e), "command": test_cmd}

    def _run_smoke(self, repo_path: str, project_config: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """
        Run smoke using runtime.*.smoke_command (if provided), with optional install_command.
        Executes real commands; assumes scripts are non-interactive and short-lived.
        """
        runtime = project_config.get("runtime", {}) if isinstance(project_config, dict) else {}
        # Prefer backend runtimes; fallback to frontend if backend not set
        backend_runtime = (
            runtime.get("backend_fastapi")
            or runtime.get("backend_php")
            or runtime.get("backend")
            or {}
        )
        frontend_runtime = runtime.get("frontend_next") or {}

        # Choose a smoke target: backend first, else frontend if present
        target = backend_runtime if backend_runtime else frontend_runtime
        if not target:
            return {"status": "skipped", "reason": "No runtime.*.smoke_command configured"}

        install_cmd = target.get("install_command")
        smoke_cmd = target.get("smoke_command")

        if not smoke_cmd:
            return {"status": "skipped", "reason": "smoke_command not configured"}

        result: Dict[str, Any] = {}

        try:
            if install_cmd:
                install_proc = subprocess.run(
                    install_cmd,
                    shell=True,
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
                result["install"] = {
                    "command": install_cmd,
                    "returncode": install_proc.returncode,
                    "stdout": install_proc.stdout,
                    "stderr": install_proc.stderr,
                }
                if install_proc.returncode != 0:
                    result["status"] = "install_failed"
                    return result

            smoke_proc = subprocess.run(
                smoke_cmd,
                shell=True,
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            result["smoke"] = {
                "command": smoke_cmd,
                "returncode": smoke_proc.returncode,
                "stdout": smoke_proc.stdout,
                "stderr": smoke_proc.stderr,
            }
            result["status"] = "passed" if smoke_proc.returncode == 0 else "failed"
            return result

        except subprocess.TimeoutExpired as e:
            return {"status": "timeout", "error": str(e)}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _create_pr(
        self,
        repo_path: str,
        feature_slug: str,
        branch_name: Optional[str],
        commit_message: str,
        push_branch: bool,
        pr_base: str,
        pr_title: Optional[str],
        pr_body: Optional[str],
        project_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Create a branch, commit changes, and optionally create a PR (real if token/repo info present).
        """
        self.repo_client.set_repo_path(repo_path)

        branch = branch_name or f"feature/{feature_slug}"
        created = self.repo_client.create_branch(branch)
        if not created:
            self.repo_client.checkout_branch(branch)

        commit_hash = self.repo_client.commit_changes(commit_message)

        # Determine repo full name from config if present
        metadata = project_config.get("metadata", {}) if isinstance(project_config, dict) else {}
        repo_full_name = metadata.get("repo_full_name") or metadata.get("github_repo")

        if push_branch and repo_full_name:
            try:
                self.repo_client.push_branch(branch)
                pr = self.repo_client.create_pull_request(
                    repo_full_name=repo_full_name,
                    head=branch,
                    base=pr_base,
                    title=pr_title or commit_message,
                    body=pr_body or "Auto-generated PR",
                )
                pr["commit"] = commit_hash
                pr["status"] = "created"
                return pr
            except Exception as e:
                # fall back to stub if push/PR fails
                return {
                    "status": "stub",
                    "branch": branch,
                    "commit": commit_hash,
                    "error": str(e),
                }

        # Stub path
        pr_stub = self.repo_client.create_pull_request_stub(
            branch_name=branch,
            title=pr_title or commit_message,
            body=pr_body or "Auto-generated PR stub."
        )
        pr_stub["commit"] = commit_hash
        return pr_stub
    
    def run_bugfix_workflow(
        self,
        project_id: str,
        run_tests: bool = True,
        run_bugfix: bool = False,
    ) -> Tuple[str, Literal["accepted", "rejected", "error"], str, Dict[str, Any]]:
        """
        Run a bugfix-only workflow.
        
        This workflow:
        - Skips ProductAgent and CodegenAgent
        - Runs tests on the current codebase
        - If tests fail and run_bugfix=True, suggests patches via BugfixAgent
        - Does NOT auto-apply patches (HITL)
        
        Args:
            project_id: Project identifier
            run_tests: Whether to run tests
            run_bugfix: Whether to suggest fixes if tests fail
            
        Returns:
            Tuple of (workflow_id, status, message, details)
        """
        workflow_id = self._generate_workflow_id(project_id)
        
        # 1. Load project config
        try:
            config = self.config_loader.load_project_config(project_id)
        except FileNotFoundError as e:
            return workflow_id, "rejected", "Project config not found", {"error": str(e)}
        
        # 2. Get repo path
        repo_path = self.config_loader.get_repo_path(project_id)
        if not repo_path:
            return workflow_id, "rejected", "Project repository not found", {
                "project_id": project_id
            }
        
        self.repo_client.set_repo_path(repo_path)
        
        details: Dict[str, Any] = {
            "project_id": project_id,
            "autopilot_config": config,
            "repo_path": repo_path,
            "workflow_steps": ["load_project_config"],
        }
        
        # 3. Run tests
        test_result = None
        tests_passed = None
        if run_tests:
            test_result = self._run_tests(repo_path, config)
            details["workflow_steps"].append("run_tests")
            details["test_result"] = test_result
            tests_passed = test_result.get("status") == "passed"
        else:
            details["workflow_steps"].append("run_tests (skipped)")
        
        # 4. If tests failed and run_bugfix=True, suggest fixes
        bugfix_result = None
        if run_tests and test_result and test_result.get("status") == "failed" and run_bugfix:
            # Get changed files from git diff (if any)
            try:
                diff = self.repo_client.get_diff()
                changed_files = self._extract_changed_files_from_diff(diff)
            except Exception:
                changed_files = []
            
            bugfix_result = self._run_bugfix(
                repo_path=repo_path,
                test_result=test_result,
                generated_files=changed_files,
                project_config=config
            )
            details["workflow_steps"].append("run_bugfix")
            details["bugfix_result"] = bugfix_result
        
        # 5. Compute workflow status
        workflow_status = self._compute_workflow_status(
            tests_passed=tests_passed,
            run_tests=run_tests,
            smoke_passed=None,
            run_smoke=False,
            governance_ok=None,
            create_pr=False
        )
        
        details["workflow_status"] = workflow_status.value if workflow_status else None
        details["tests_passed"] = tests_passed
        details["smoke_passed"] = None
        details["governance_ok"] = None
        
        return workflow_id, "accepted", "Bugfix workflow executed", details
    
    def _extract_changed_files_from_diff(self, diff: str) -> List[str]:
        """Extract list of changed files from unified diff."""
        files = []
        for line in diff.split("\n"):
            if line.startswith("---") or line.startswith("+++"):
                file_path = line.replace("---", "").replace("+++", "").strip()
                file_path = file_path.lstrip("a/").lstrip("b/")
                if file_path and file_path != "/dev/null" and file_path not in files:
                    files.append(file_path)
        return files

    def _run_bugfix(
        self,
        repo_path: str,
        test_result: Dict[str, Any],
        generated_files: List[str],
        project_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run bugfix agent to suggest fixes for test failures.
        
        Args:
            repo_path: Repository path
            test_result: Test execution result
            generated_files: List of files that were generated
            project_config: Project configuration
            
        Returns:
            dict: Bugfix result with patches
        """
        try:
            request = BugfixRequest(
                command=test_result.get("command", ""),
                exit_code=test_result.get("returncode", 1),
                stdout=test_result.get("stdout", ""),
                stderr=test_result.get("stderr", ""),
                changed_files=generated_files,
                project_config=project_config
            )
            response = self.bugfix_agent.suggest_fixes(request)
            
            return {
                "success": response.success,
                "patches": [
                    {
                        "file_path": p.file_path,
                        "unified_diff": p.unified_diff,
                        "notes": p.notes
                    }
                    for p in response.patches
                ],
                "retry_command": response.retry_command,
                "notes": response.notes
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "patches": []
            }
