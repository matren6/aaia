"""
OpenAI Provider for AAIA LLM Integration

Handles OpenAI API and OpenAI-compatible endpoints (LocalAI, LM Studio, etc.)
Provides access to GPT-4, GPT-3.5, and other advanced models.
"""

import requests
from typing import Optional, List
from .base_provider import BaseLLMProvider, LLMResponse, ModelInfo



class OpenAIProvider(BaseLLMProvider):
    """OpenAI provider for cloud-based model inference

    Supports:
    - OpenAI API (GPT-4, GPT-3.5, etc.)
    - Azure OpenAI
    - Any OpenAI-compatible endpoint (LocalAI, LM Studio, etc.)

    Features:
    - Advanced model capabilities
    - Pay-per-token pricing
    - Streaming support (optional)
    """

    OPENAI_MODELS = [
        ModelInfo(
            id='gpt-4o',
            name='GPT-4o',
            provider='openai',
            capabilities={'code': True, 'reasoning': True, 'vision': True, 'function_calling': True},
            context_window=128000,
            input_cost_per_1k=2.50,
            output_cost_per_1k=10.00,
            currency='USD',
            description='Most capable GPT-4 model with vision',
            parameter_count='~1T'
        ),
        ModelInfo(
            id='gpt-4o-mini',
            name='GPT-4o Mini',
            provider='openai',
            capabilities={'code': True, 'reasoning': True, 'vision': False, 'function_calling': True},
            context_window=128000,
            input_cost_per_1k=0.15,
            output_cost_per_1k=0.60,
            currency='USD',
            description='Fast and affordable GPT-4 class model',
            parameter_count='~8B'
        ),
        ModelInfo(
            id='gpt-3.5-turbo',
            name='GPT-3.5 Turbo',
            provider='openai',
            capabilities={'code': True, 'reasoning': False, 'vision': False, 'function_calling': True},
            context_window=16384,
            input_cost_per_1k=0.50,
            output_cost_per_1k=1.50,
            currency='USD',
            description='Legacy fast model for simple tasks'
        ),
    ]

    def __init__(self, config):
        """Initialize OpenAI provider


            config: OpenAIConfig with api_key, base_url, model, etc.
        """
        self.config = config
        self.api_key = config.api_key
        self.base_url = config.base_url.rstrip('/')
        self.timeout = config.timeout
        self.max_retries = config.max_retries
        self.organization = getattr(config, 'organization', None)
    
    def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> LLMResponse:
        """Generate completion using OpenAI API
        
        Args:
            prompt: User prompt
            system_prompt: System prompt
            **kwargs: Optional parameters (model, temperature, max_tokens, etc.)
            
        Returns:
            LLMResponse with generated content and token counts
        """
        model = kwargs.get("model", self.config.default_model)
        max_tokens = kwargs.get("max_tokens", getattr(self.config, 'max_tokens', 4096))
        temperature = kwargs.get("temperature", 0.7)
        
        # Prepare request headers
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        if self.organization:
            headers["OpenAI-Organization"] = self.organization
        
        # Prepare messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Prepare payload
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        # Add optional parameters
        if "top_p" in kwargs:
            payload["top_p"] = kwargs["top_p"]
        if "frequency_penalty" in kwargs:
            payload["frequency_penalty"] = kwargs["frequency_penalty"]
        if "presence_penalty" in kwargs:
            payload["presence_penalty"] = kwargs["presence_penalty"]
        
        try:
            # Make API request
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Extract response
            content = data["choices"][0]["message"]["content"]
            
            # Extract token counts
            usage = data.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", input_tokens + output_tokens)
            
            # Calculate cost
            cost = self._calculate_cost(model, input_tokens, output_tokens)
            
            return LLMResponse(
                content=content,
                model=model,
                tokens_used=total_tokens,
                cost=cost,
                provider="openai",
                metadata={
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "model_id": data.get("model", model),
                    "finish_reason": data["choices"][0].get("finish_reason", "stop")
                }
            )
        
        except requests.exceptions.ConnectionError:
            raise RuntimeError(f"Cannot connect to OpenAI API at {self.base_url}")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise RuntimeError("Invalid API key. Check OPENAI_API_KEY configuration.")
            elif e.response.status_code == 429:
                raise RuntimeError("Rate limited by OpenAI API. Please wait before retrying.")
            else:
                raise RuntimeError(f"OpenAI API error: {e.response.text}")
        except requests.exceptions.Timeout:
            raise RuntimeError(f"OpenAI request timed out (timeout: {self.timeout}s)")
        except Exception as e:
            raise RuntimeError(f"OpenAI inference failed: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if OpenAI API is accessible
        
        Returns:
            True if API key is set and endpoint is reachable
        """
        if not self.config.enabled or not self.api_key:
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Try to list models to verify connection
            response = requests.get(
                f"{self.base_url}/models",
                headers=headers,
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def get_cost_per_token(self, model: str) -> float:
        """Get cost per token for OpenAI models
        
        Args:
            model: Model name
            
        Returns:
            Cost in USD per token (approximate)
        """
        # Pricing as of 2024 (in USD per 1M tokens)
        # These are approximations - check OpenAI pricing for current rates
        pricing = {
            # GPT-4o
            "gpt-4o": 0.005,  # per 1k tokens average
            "gpt-4o-mini": 0.00015,  # very cheap
            "gpt-4o-mini-2024-07-18": 0.00015,
            
            # GPT-4
            "gpt-4": 0.03,
            "gpt-4-turbo": 0.01,
            "gpt-4-turbo-preview": 0.01,
            "gpt-4-32k": 0.06,
            
            # GPT-3.5
            "gpt-3.5-turbo": 0.0005,
            "gpt-3.5-turbo-16k": 0.003,
            
            # Default
            "default": 0.001
        }
        
        return pricing.get(model, pricing.get("default", 0.001)) / 1000  # Convert to per-token

    def get_available_models(self) -> List[ModelInfo]:
        """Return static OpenAI model pricing table"""
        return list(self.OPENAI_MODELS)

    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for a request

        Args:
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Cost in USD
        """
        # For simplicity, use average cost per token
        # Real implementation would separate input/output pricing
        cost_per_token = self.get_cost_per_token(model)
        total_tokens = input_tokens + output_tokens
        return total_tokens * cost_per_token
