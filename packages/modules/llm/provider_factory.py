"""
Provider Factory for AAIA LLM Integration

Manages creation and lifecycle of LLM providers.
Implements factory pattern with fallback chain support.
"""

from typing import Optional, List, Dict
from .base_provider import BaseLLMProvider


class ProviderFactory:
    """Factory for creating and managing LLM providers
    
    Handles:
    - Initialization of enabled providers
    - Provider selection and routing
    - Fallback chain management
    - Provider availability checking
    """
    
    def __init__(self, config):
        """Initialize provider factory
        
        Args:
            config: LLMConfig object with provider configurations
        """
        self.config = config
        self._providers: Dict[str, BaseLLMProvider] = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize all enabled providers"""
        # Import here to avoid circular imports
        from .ollama_provider import OllamaProvider
        from .openai_provider import OpenAIProvider
        from .github_provider import GitHubProvider
        from .azure_provider import AzureOpenAIProvider
        from .venice_provider import VeniceProvider
        
        # Initialize Ollama
        if self.config.ollama.enabled:
            try:
                self._providers['ollama'] = OllamaProvider(self.config.ollama)
            except Exception as e:
                print(f"Warning: Failed to initialize Ollama provider: {e}")
        
        # Initialize OpenAI
        if self.config.openai.enabled:
            try:
                self._providers['openai'] = OpenAIProvider(self.config.openai)
            except Exception as e:
                print(f"Warning: Failed to initialize OpenAI provider: {e}")
        
        # Initialize GitHub
        if self.config.github.enabled:
            try:
                self._providers['github'] = GitHubProvider(self.config.github)
            except Exception as e:
                print(f"Warning: Failed to initialize GitHub provider: {e}")
        
        # Initialize Azure
        if self.config.azure.enabled:
            try:
                self._providers['azure'] = AzureOpenAIProvider(self.config.azure)
            except Exception as e:
                print(f"Warning: Failed to initialize Azure provider: {e}")
        
        # Initialize Venice
        if hasattr(self.config, 'venice') and self.config.venice.enabled:
            try:
                self._providers['venice'] = VeniceProvider(self.config.venice)
            except Exception as e:
                print(f"Warning: Failed to initialize Venice provider: {e}")
    
    def get_provider(self, name: Optional[str] = None) -> BaseLLMProvider:
        """Get a provider by name, or use default/fallback chain
        
        Args:
            name: Provider name (ollama, openai, github, azure, venice)
                 If None, uses default_provider
                 
        Returns:
            BaseLLMProvider instance
            
        Raises:
            ValueError: If provider not found
            RuntimeError: If provider unavailable and no fallback
        """
        provider_name = name or self.config.default_provider
        
        # Validate provider exists
        if provider_name not in self._providers:
            if self.config.fallback_provider:
                print(f"Warning: Provider '{provider_name}' not available, using fallback")
                return self.get_provider(self.config.fallback_provider)
            raise ValueError(f"Provider '{provider_name}' not available or not enabled")
        
        provider = self._providers[provider_name]
        
        # Check provider availability
        if not provider.is_available():
            if self.config.fallback_provider:
                print(f"Warning: Provider '{provider_name}' is not accessible, using fallback")
                return self.get_provider(self.config.fallback_provider)
            raise RuntimeError(
                f"Provider '{provider_name}' is not available. "
                f"Check configuration and API keys."
            )
        
        return provider
    
    def list_available_providers(self) -> List[str]:
        """List all available and functional providers
        
        Returns:
            List of provider names that are configured and accessible
        """
        available = []
        for name, provider in self._providers.items():
            try:
                if provider.is_available():
                    available.append(name)
            except Exception:
                pass
        return available
    
    def list_configured_providers(self) -> List[str]:
        """List all configured providers (may not be accessible)
        
        Returns:
            List of provider names that are enabled in configuration
        """
        return list(self._providers.keys())
    
    def get_provider_info(self, name: str) -> Optional[Dict]:
        """Get information about a specific provider
        
        Args:
            name: Provider name
            
        Returns:
            Dict with provider info or None if not found
        """
        if name not in self._providers:
            return None
        
        provider = self._providers[name]
        return {
            'name': name,
            'available': provider.is_available(),
            'type': type(provider).__name__
        }
