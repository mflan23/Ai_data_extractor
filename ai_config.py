"""
AI Configuration and Secrets Management
Handles API keys and model configuration for AI integration.
"""
import os
from typing import Dict, Optional, List
from enum import Enum


class AIProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE_GEMINI = "google_gemini"
    LOCAL = "local"


class AIConfig:
    """Configuration for AI model integration."""
    
    def __init__(self):
        self.provider: Optional[AIProvider] = None
        self.api_key: Optional[str] = None
        self.base_url: Optional[str] = None
        self.model: Optional[str] = None
        self.timeout: int = 60
        self.max_retries: int = 3
    
    @classmethod
    def from_env(cls) -> 'AIConfig':
        """Load configuration from environment variables."""
        config = cls()
        
        # Detect provider from API key presence
        if os.getenv('OPENAI_API_KEY'):
            config.provider = AIProvider.OPENAI
            config.api_key = os.getenv('OPENAI_API_KEY', '')
            config.model = os.getenv('OPENAI_MODEL', 'gpt-4o')
        elif os.getenv('ANTHROPIC_API_KEY'):
            config.provider = AIProvider.ANTHROPIC
            config.api_key = os.getenv('ANTHROPIC_API_KEY', '')
            config.model = os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20240620')
        elif os.getenv('GEMINI_API_KEY'):
            config.provider = AIProvider.GOOGLE_GEMINI
            config.api_key = os.getenv('GEMINI_API_KEY', '')
            config.model = os.getenv('GEMINI_MODEL', 'gemini-1.5-pro')
        elif os.getenv('LOCAL_AI_ENABLED'):
            config.provider = AIProvider.LOCAL
            config.base_url = os.getenv('LOCAL_AI_URL', 'http://localhost:11434')
            config.model = os.getenv('LOCAL_AI_MODEL', 'llama3')
        
        return config
    
    def is_available(self) -> bool:
        """Check if the configured AI provider is available."""
        if not self.provider:
            return False
        
        if self.provider == AIProvider.LOCAL:
            return bool(self.base_url and self.model)
        
        return bool(self.api_key and self.model)
    
    def get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        headers = {}
        
        if self.provider == AIProvider.OPENAI:
            headers['Authorization'] = f'Bearer {self.api_key}'
        elif self.provider == AIProvider.ANTHROPIC:
            headers['x-api-key'] = self.api_key
        elif self.provider == AIProvider.GOOGLE_GEMINI:
            headers['Authorization'] = f'Bearer {self.api_key}'
        
        return headers
    
    def get_model_name(self) -> str:
        """Get the model name for the current provider."""
        if self.provider == AIProvider.LOCAL:
            return f"{self.base_url}/api/generate"
        return self.model or "unknown"


# Global configuration instance
config = AIConfig.from_env()

# Helper function to check if AI is available
def is_ai_available() -> bool:
    return config.is_available()


# Helper function to get current provider
def get_current_provider() -> Optional[str]:
    return config.provider.value if config.provider else None


# Helper function to get current model
def get_current_model() -> str:
    return config.get_model_name()


# Function to update configuration
def update_config(provider: AIProvider, api_key: str, model: str = ""):
    """Update AI configuration with new credentials."""
    config.provider = provider
    config.api_key = api_key
    config.model = model if model else config.model
    
    if provider == AIProvider.LOCAL:
        config.base_url = os.getenv('LOCAL_AI_URL')
    
    return config.is_available()
