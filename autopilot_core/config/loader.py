import os
import yaml
import tempfile
from typing import Any, Dict, Optional
from autopilot_core.config.project_registry import ProjectRegistry
from autopilot_core.clients.repo_client import RepoClient


class ConfigLoader:
    """
    Loads per-project autopilot.yaml configurations.
    
    Supports both:
    - Local paths (for development/testing): configs/examples/<project_id>/.sanjaya/autopilot.yaml
    - GitHub repos: clones repo and loads .sanjaya/autopilot.yaml from it
    """

    BASE_PATH = "configs/examples"
    CACHE_DIR = ".cache/projects"

    def __init__(self, project_registry: Optional[ProjectRegistry] = None, github_token: Optional[str] = None):
        """
        Initialize config loader.
        
        Args:
            project_registry: Project registry instance (optional)
            github_token: GitHub token for accessing private repos
        """
        self.project_registry = project_registry or ProjectRegistry()
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.repo_client = RepoClient(github_token=self.github_token)
        self._cache: Dict[str, str] = {}  # project_id -> cached repo path
        
        # Ensure cache directory exists
        os.makedirs(self.CACHE_DIR, exist_ok=True)

    def load_project_config(self, project_id: str) -> Dict[str, Any]:
        """
        Load the .sanjaya/autopilot.yaml file for the given project_id.
        
        First checks project registry for GitHub repo, then falls back to local path.
        
        Args:
            project_id: Project identifier
            
        Returns:
            dict: Project configuration
            
        Raises:
            FileNotFoundError: If config file not found
        """
        # Check if project is registered (GitHub repo)
        project_info = self.project_registry.get_project(project_id)
        
        if project_info:
            # Load from GitHub repo
            return self.load_from_github(project_info["repo_url"], project_id)
        else:
            # Fall back to local path (for testing/development)
            return self.load_from_local(project_id)

    def load_from_github(self, repo_url: str, project_id: str) -> Dict[str, Any]:
        """
        Load config from GitHub repository.
        
        Args:
            repo_url: GitHub repository URL
            project_id: Project identifier
            
        Returns:
            dict: Project configuration
            
        Raises:
            FileNotFoundError: If config file not found
            RuntimeError: If repo clone/access fails
        """
        # Check cache first
        if project_id in self._cache:
            cached_path = self._cache[project_id]
            if os.path.exists(cached_path):
                config_path = os.path.join(cached_path, ".sanjaya", "autopilot.yaml")
                if os.path.exists(config_path):
                    with open(config_path, "r") as f:
                        return yaml.safe_load(f) or {}
        
        # Clone repo to cache
        cache_path = os.path.join(self.CACHE_DIR, project_id)
        if not os.path.exists(cache_path):
            self.repo_client.clone_repository(repo_url, cache_path)
        
        self._cache[project_id] = cache_path
        self.repo_client.set_repo_path(cache_path)
        
        # Load config
        config_path = os.path.join(cache_path, ".sanjaya", "autopilot.yaml")
        if not os.path.exists(config_path):
            raise FileNotFoundError(
                f"autopilot.yaml not found in repo '{repo_url}' at .sanjaya/autopilot.yaml"
            )
        
        with open(config_path, "r") as f:
            return yaml.safe_load(f) or {}

    def load_from_local(self, project_id: str) -> Dict[str, Any]:
        """
        Load config from local path (for development/testing).
        
        Args:
            project_id: Project identifier
            
        Returns:
            dict: Project configuration
            
        Raises:
            FileNotFoundError: If config file not found
        """
        project_root = os.path.join(self.BASE_PATH, project_id, ".sanjaya")
        config_path = os.path.join(project_root, "autopilot.yaml")

        if not os.path.exists(config_path):
            raise FileNotFoundError(
                f"autopilot.yaml not found for project '{project_id}' at {config_path}. "
                f"Project may need to be registered as a GitHub repo."
            )

        with open(config_path, "r") as f:
            return yaml.safe_load(f) or {}
    
    def get_repo_path(self, project_id: str) -> Optional[str]:
        """
        Get the local path to a project's repository (cached or local).
        
        Args:
            project_id: Project identifier
            
        Returns:
            str: Path to repository, or None if not found
        """
        # Check cache
        if project_id in self._cache:
            return self._cache[project_id]
        
        # Check registry
        project_info = self.project_registry.get_project(project_id)
        if project_info:
            cache_path = os.path.join(self.CACHE_DIR, project_id)
            if os.path.exists(cache_path):
                return cache_path
        
        # Check local path
        local_path = os.path.join(self.BASE_PATH, project_id)
        if os.path.exists(local_path):
            return local_path
        
        return None
