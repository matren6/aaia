"""
Azure OpenAI Provider for AAIA LLM Integration

Handles Azure OpenAI Service - enterprise deployment option.
"""

import requests
from typing import List
from .base_provider import BaseLLMProvider, LLMResponse, ModelInfo


class AzureOpenAIProvider(BaseLLMProvider):
    """Azure OpenAI provider for enterprise deployments
    
    Features:
    - Enterprise SLAs and support
    - Same models as OpenAI but deployed in Azure
    - Different authentication model
    - HIPAA/SOC2 compliance options
    """
    
    def __init__(self, config):
        """Initialize Azure OpenAI provider
        
        Args:
            config: AzureOpenAIConfig with endpoint, key, deployment, etc.
        """
        self.config = config
        self.api_key = config.api_key
        self.endpoint = config.endpoint.rstrip('/')
        self.deployment_name = config.deployment_name
        self.api_version = getattr(config, 'api_version', '2024-02-01')
        self.timeout = config.timeout
        self.max_retries = config.max_retries
    
    def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> LLMResponse:
        """Generate completion using Azure OpenAI
        
        Args:
            prompt: User prompt
            system_prompt: System prompt
            **kwargs: Optional parameters
            
        Returns:
            LLMResponse with generated content
        """
        max_tokens = kwargs.get("max_tokens", 4096)
        temperature = kwargs.get("temperature", 0.7)
        
        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        try:
            url = (
                f"{self.endpoint}/openai/deployments/{self.deployment_name}/"
                f"chat/completions?api-version={self.api_version}"
            )
            
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            data = response.json()
            
            content = data["choices"][0]["message"]["content"]
            tokens = data["usage"]["total_tokens"]
            
            # Calculate cost based on model pricing
            cost = self._calculate_cost(tokens)
            
            return LLMResponse(
                content=content,
                model=self.deployment_name,
                tokens_used=tokens,
                cost=cost,
                provider="azure",
                metadata=data
            )
        
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise RuntimeError("Invalid Azure API key")
            else:
                raise RuntimeError(f"Azure API error: {e.response.text}")
        except Exception as e:
            raise RuntimeError(f"Azure OpenAI request failed: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if Azure OpenAI is accessible
        
        Returns:
            True if endpoint and credentials are valid
        """
        if not self.config.enabled or not self.api_key or not self.deployment_name:
            return False
        
        try:
            # Just check if endpoint responds
            headers = {"api-key": self.api_key}
            url = (
                f"{self.endpoint}/openai/deployments/{self.deployment_name}/"
                f"models?api-version={self.api_version}"
            )
            
            response = requests.get(
                url,
                headers=headers,
                timeout=5
            )
            return response.status_code in [200, 404]  # 404 is ok for this check
        except Exception:
            return False

    def get_available_models(self) -> List[ModelInfo]:
        """Get Azure OpenAI deployment"""
        return [ModelInfo(
            id=self.config.deployment_name or 'gpt-4',
            name=f'Azure {self.config.deployment_name}',
            provider='azure',
            capabilities={'code': True, 'reasoning': True, 'vision': False, 'function_calling': True},
            context_window=8192,
            input_cost_per_1k=2.50,
            output_cost_per_1k=10.00,
            currency='USD'
        )]

    def get_cost_per_token(self, model: str) -> float:
        """Get cost per token for Azure OpenAI

        Args:
            model: Model/deployment name

        Returns:
            Cost in USD per token (depends on deployment)
        """
        # Similar to OpenAI pricing, varies by deployment
        return 0.001

    def _calculate_cost(self, tokens: int) -> float:
        """Calculate cost for tokens

        Args:
            tokens: Number of tokens

        Returns:
            Cost in USD
        """
        return tokens * self.get_cost_per_token(self.deployment_name)
