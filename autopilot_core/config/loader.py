import os
import yaml
from typing import Any, Dict

class ConfigLoader:
    """
    Loads per-project autopilot.yaml configurations.

    For now, we assume all example projects live under:
    configs/examples/<project_id>/.sanjaya/autopilot.yaml
    """

    BASE_PATH = "configs/examples"

    def __init__(self):
        pass

    def load_project_config(self, project_id: str) -> Dict[str, Any]:
        """
        Load the .sanjaya/autopilot.yaml file for the given project_id.
        Returns dict.

        Raises FileNotFoundError if missing.
        """
        project_root = os.path.join(self.BASE_PATH, project_id, ".sanjaya")
        config_path = os.path.join(project_root, "autopilot.yaml")

        if not os.path.exists(config_path):
            raise FileNotFoundError(
                f"autopilot.yaml not found for project '{project_id}' at {config_path}"
            )

        with open(config_path, "r") as f:
            return yaml.safe_load(f) or {}
