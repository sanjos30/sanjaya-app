"""Client for LLM API interactions."""


class LLMClient:
    """Client for LLM operations."""
    
    def __init__(self, api_key: str, model: str = None):
        """
        Initialize LLM client.
        
        Args:
            api_key: API key for LLM service
            model: Model name to use
        """
        pass
    
    def generate(self, prompt: str, context: dict = None):
        """
        Generate text using LLM.
        
        Args:
            prompt: Input prompt
            context: Additional context
            
        Returns:
            str: Generated text
        """
        pass
    
    def chat(self, messages: list):
        """
        Chat with LLM using message history.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            str: LLM response
        """
        pass

