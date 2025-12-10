"""Client for LLM API interactions with support for multiple providers."""

import os
from typing import Optional, List, Dict, Any
from enum import Enum


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class LLMClient:
    """Generic LLM client supporting multiple providers."""
    
    def __init__(
        self,
        provider: str = "openai",
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        """
        Initialize LLM client.
        
        Args:
            provider: Provider name ("openai" or "anthropic")
            api_key: API key for LLM service (defaults to env var)
            model: Model name to use (defaults to provider default)
            
        Raises:
            ImportError: If required provider library is not installed
            ValueError: If provider is not supported
        """
        self.provider = provider.lower()
        
        # Get API key from parameter or environment
        if api_key:
            self.api_key = api_key
        elif self.provider == LLMProvider.OPENAI:
            self.api_key = os.getenv("OPENAI_API_KEY")
        elif self.provider == LLMProvider.ANTHROPIC:
            self.api_key = os.getenv("ANTHROPIC_API_KEY")
        else:
            self.api_key = None
        
        if not self.api_key:
            raise ValueError(
                f"API key required for {provider}. "
                f"Set {provider.upper()}_API_KEY environment variable or pass api_key parameter."
            )
        
        # Set default model if not provided
        if model:
            self.model = model
        elif self.provider == LLMProvider.OPENAI:
            self.model = os.getenv("OPENAI_MODEL", "gpt-4")
        elif self.provider == LLMProvider.ANTHROPIC:
            self.model = os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229")
        else:
            self.model = model
        
        # Initialize provider-specific client
        self._client = self._init_client()
    
    def _init_client(self):
        """Initialize provider-specific client."""
        if self.provider == LLMProvider.OPENAI:
            try:
                from openai import OpenAI
                return OpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "OpenAI library not installed. Install with: pip install openai"
                )
        elif self.provider == LLMProvider.ANTHROPIC:
            try:
                import anthropic
                return anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "Anthropic library not installed. Install with: pip install anthropic"
                )
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Generate text using LLM.
        
        Args:
            prompt: Input prompt
            system_prompt: System prompt (optional)
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters
            
        Returns:
            str: Generated text
        """
        if self.provider == LLMProvider.OPENAI:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            return response.choices[0].message.content
        
        elif self.provider == LLMProvider.ANTHROPIC:
            system_msg = system_prompt or ""
            response = self._client.messages.create(
                model=self.model,
                max_tokens=max_tokens or 4096,
                temperature=temperature,
                system=system_msg,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
            return response.content[0].text
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Chat with LLM using message history.
        
        Args:
            messages: List of message dictionaries with "role" and "content"
            system_prompt: System prompt (optional)
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters
            
        Returns:
            str: LLM response
        """
        if self.provider == LLMProvider.OPENAI:
            message_list = []
            if system_prompt:
                message_list.append({"role": "system", "content": system_prompt})
            message_list.extend(messages)
            
            response = self._client.chat.completions.create(
                model=self.model,
                messages=message_list,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            return response.choices[0].message.content
        
        elif self.provider == LLMProvider.ANTHROPIC:
            system_msg = system_prompt or ""
            response = self._client.messages.create(
                model=self.model,
                max_tokens=max_tokens or 4096,
                temperature=temperature,
                system=system_msg,
                messages=messages,
                **kwargs
            )
            return response.content[0].text

