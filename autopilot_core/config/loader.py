"""Loader for project autopilot.yaml configuration files."""


class ConfigLoader:
    """Loads and validates project autopilot.yaml configurations."""
    
    def __init__(self):
        """Initialize config loader."""
        pass
    
    def load_project_config(self, project_path: str):
        """
        Load autopilot.yaml from a project.
        
        Args:
            project_path: Path to project root
            
        Returns:
            dict: Project configuration
        """
        pass
    
    def validate_config(self, config: dict):
        """
        Validate configuration against schema.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            tuple: (is_valid, errors)
        """
        pass

