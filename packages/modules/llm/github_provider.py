"""
GitHub Models Provider for AAIA LLM Integration

Access to GitHub Models API - currently FREE during preview.
Supports various models through GitHub's inference service.
"""

import requests
from typing import List
from .base_provider import BaseLLMProvider, LLMResponse, ModelInfo


class GitHubProvider(BaseLLMProvider):
    """GitHub Models API provider
    
    Features:
    - Currently FREE during preview
    - OpenAI-compatible API
    - Access to multiple models (Claude, GPT, etc.)
    - Good for development and testing
    """
    
    def __init__(self, config):
        """Initialize GitHub Models provider

        Args:
            config: GitHubModelsConfig with api_key, model, etc.
        """
        self.config = config
        self.api_key = config.api_key
        self.base_url = "https://models.github.ai/orgs/Integrated-Worlds"
        self.timeout = config.timeout
        self.max_retries = config.max_retries
    
    def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> LLMResponse:
        """Generate completion using GitHub Models API
        
        Args:
            prompt: User prompt
            system_prompt: System prompt
            **kwargs: Optional parameters
            
        Returns:
            LLMResponse with generated content
        """
        model = kwargs.get("model", self.config.default_model)
        max_tokens = kwargs.get("max_tokens", 4096)
        temperature = kwargs.get("temperature", 0.7)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/inference/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            data = response.json()
            
            content = data["choices"][0]["message"]["content"]
            tokens = data["usage"]["total_tokens"]
            
            # GitHub Models is FREE during preview
            cost = 0.0
            
            return LLMResponse(
                content=content,
                model=model,
                tokens_used=tokens,
                cost=cost,
                provider="github",
                metadata=data
            )
        
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise RuntimeError("Invalid GitHub API token")
            else:
                raise RuntimeError(f"GitHub API error: {e.response.text}")
        except Exception as e:
            raise RuntimeError(f"GitHub Models request failed: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if GitHub Models API is accessible

        Returns:
            True if API is reachable with valid credentials
        """
        if not self.config.enabled or not self.api_key:
            return False

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28"
            }
            # Try a simple inference request to check availability
            # Using the models endpoint might not work with org URL
            response = requests.get(
                "https://models.github.ai/v1/models",
                headers=headers,
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False

    def get_available_models(self) -> List[ModelInfo]:
        """Get GitHub Models"""
        return [ModelInfo(
            id=self.config.default_model,
            name=f'GitHub {self.config.default_model}',
            provider='github',
            capabilities={'code': True, 'reasoning': True, 'vision': False, 'function_calling': True},
            context_window=128000,
            input_cost_per_1k=0.0,
            output_cost_per_1k=0.0,
            currency='FREE'
        )]

    def get_cost_per_token(self, model: str) -> float:
        """Get cost per token for GitHub Models

        Args:
            model: Model name

        Returns:
            0.0 (FREE during preview)
        """
        return 0.0
