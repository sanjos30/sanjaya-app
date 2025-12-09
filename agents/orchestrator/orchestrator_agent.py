import os
from typing import Tuple, Literal, Dict, Any
from datetime import datetime

from autopilot_core.config.loader import ConfigLoader

class OrchestratorAgent:
    """
    OrchestratorAgent coordinates workflows between agents.

    Step 2 Version:
    - Loads project config
    - Validates design contract file exists
    - Returns a structured workflow plan
    """

    def __init__(self):
        self.config_loader = ConfigLoader()

    def run_feature_workflow(
        self,
        project_id: str,
        contract_path: str,
        dry_run: bool = True,
    ) -> Tuple[str, Literal["accepted", "rejected", "error"], str, Dict[str, Any]]:

        workflow_id = self._generate_workflow_id(project_id)

        # 1. Load project config
        try:
            config = self.config_loader.load_project_config(project_id)
        except FileNotFoundError as e:
            return workflow_id, "rejected", "Project config not found", {"error": str(e)}

        # 2. Verify contract file exists
        full_contract_path = os.path.join(
            "configs/examples", project_id, ".sanjaya", contract_path
        )

        if not os.path.exists(full_contract_path):
            return workflow_id, "rejected", "Design contract missing", {
                "expected_path": full_contract_path
            }

        # 3. Stub workflow response
        details: Dict[str, Any] = {
            "project_id": project_id,
            "autopilot_config": config,
            "design_contract": contract_path,
            "dry_run": dry_run,
            "workflow_steps": [
                "load_project_config",
                "validate_contract_exists",
                "prepare_codegen_inputs",
                "invoke_codegen_agent (stub)",
                "run_tests (stub)",
                "prepare_pull_request (stub)"
            ],
        }

        return workflow_id, "accepted", "Feature workflow validated (stub)", details

    def _generate_workflow_id(self, project_id: str) -> str:
        ts = datetime.utcnow().isoformat()
        return f"wf-{project_id}-{ts}"
