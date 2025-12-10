"""Project registry for tracking registered projects."""

import json
import os
from typing import Dict, List, Optional


class ProjectRegistry:
    """
    Registry for tracking projects registered with Sanjaya.
    
    Stores project metadata including repo URLs, project IDs, and configuration.
    Uses a simple JSON file for persistence.
    """
    
    def __init__(self, registry_file: str = ".sanjaya/project_registry.json"):
        """
        Initialize project registry.
        
        Args:
            registry_file: Path to registry JSON file
        """
        self.registry_file = registry_file
        self._ensure_registry_dir()
        self._projects: Dict[str, Dict] = {}
        self._load_registry()
    
    def _ensure_registry_dir(self):
        """Ensure the registry directory exists."""
        registry_dir = os.path.dirname(self.registry_file)
        if registry_dir and not os.path.exists(registry_dir):
            os.makedirs(registry_dir, exist_ok=True)
    
    def _load_registry(self):
        """Load registry from file."""
        if os.path.exists(self.registry_file):
            try:
                with open(self.registry_file, 'r') as f:
                    self._projects = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._projects = {}
        else:
            self._projects = {}
    
    def _save_registry(self):
        """Save registry to file."""
        try:
            with open(self.registry_file, 'w') as f:
                json.dump(self._projects, f, indent=2)
        except IOError as e:
            raise RuntimeError(f"Failed to save registry: {e}")
    
    def register_project(
        self,
        project_id: str,
        repo_url: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Register a new project.
        
        Args:
            project_id: Unique project identifier
            repo_url: GitHub repository URL (e.g., "https://github.com/user/repo.git")
            metadata: Additional project metadata
            
        Returns:
            dict: Registered project information
            
        Raises:
            ValueError: If project_id already exists
        """
        if project_id in self._projects:
            raise ValueError(f"Project '{project_id}' is already registered")
        
        project_info = {
            "project_id": project_id,
            "repo_url": repo_url,
            "metadata": metadata or {},
            "registered_at": None  # Could add timestamp if needed
        }
        
        self._projects[project_id] = project_info
        self._save_registry()
        
        return project_info
    
    def get_project(self, project_id: str) -> Optional[Dict]:
        """
        Get project information by project_id.
        
        Args:
            project_id: Project identifier
            
        Returns:
            dict: Project information or None if not found
        """
        return self._projects.get(project_id)
    
    def list_projects(self) -> List[Dict]:
        """
        List all registered projects.
        
        Returns:
            list: List of project information dictionaries
        """
        return list(self._projects.values())
    
    def unregister_project(self, project_id: str) -> bool:
        """
        Unregister a project.
        
        Args:
            project_id: Project identifier
            
        Returns:
            bool: True if project was removed, False if not found
        """
        if project_id in self._projects:
            del self._projects[project_id]
            self._save_registry()
            return True
        return False
    
    def update_project_metadata(self, project_id: str, metadata: Dict) -> bool:
        """
        Update project metadata.
        
        Args:
            project_id: Project identifier
            metadata: Metadata to update (will be merged with existing)
            
        Returns:
            bool: True if project was updated, False if not found
        """
        if project_id not in self._projects:
            return False
        
        self._projects[project_id]["metadata"].update(metadata)
        self._save_registry()
        return True

