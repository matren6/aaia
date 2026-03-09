"""
Venice AI Provider for AAIA LLM Integration

Privacy-focused AI provider with DIEM-based credit system.
Requires VVV token staking for daily DIEM allocation.

Cost Model:
- Stake VVV tokens → Earn daily DIEM allocation
- 1 DIEM ≈ $631 USD (as of 2024)
- Example: ~$2000 VVV staked → 0.49 DIEM/day
- Not free - requires token investment

Learn more:
- https://venice.ai/blog/understanding-venice-compute-units-vcu
- https://venice.ai/lp/diem

Supports OpenAI-compatible chat completions API with model discovery.
"""

import requests
from typing import Optional, Dict, List
from datetime import datetime
from .base_provider import ModelInfo

from .base_provider import BaseLLMProvider, LLMResponse


class VeniceAPIClient:
    """Client for Venice AI specific endpoints"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.venice.ai/api/v1"):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self._cached_models = None
        self._cached_diem_status = None
        self._cached_compatibility = None
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make authenticated request to Venice API"""
        headers = kwargs.pop('headers', {})
        headers['Authorization'] = f'Bearer {self.api_key}'
        headers.setdefault('Content-Type', 'application/json')
        
        url = f"{self.base_url}{endpoint}"
        response = requests.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()
        return response.json()
    
    def get_rate_limits(self, force_refresh: bool = False) -> Dict:
        """Get DIEM balance and rate limits"""
        if not force_refresh and self._cached_diem_status:
            return self._cached_diem_status

        data = self._make_request('GET', '/api_keys/rate_limits')
        self._cached_diem_status = data
        return data

    def get_models(self, force_refresh: bool = False) -> list:
        """Get list of available models with pricing"""
        if not force_refresh and self._cached_models:
            return self._cached_models

        response = self._make_request('GET', '/models')
        models = response.get('data', [])
        self._cached_models = models
        return models
    
    def get_compatibility_mapping(self) -> Dict:
        """Get model name compatibility mapping"""
        if self._cached_compatibility:
            return self._cached_compatibility

        response = self._make_request('GET', '/models/compatibility_mapping')
        mapping = response.get('data', {})
        self._cached_compatibility = mapping
        return mapping
    
    def resolve_model_name(self, model: str) -> str:
        """Resolve model name through compatibility mapping"""
        mapping = self.get_compatibility_mapping()
        return mapping.get(model, model)
    
    def get_model_pricing(self, model_id: str) -> Optional[Dict]:
        """Get pricing for specific model"""
        models = self.get_models()
        for model in models:
            if model.get('id') == model_id:
                return model.get('model_spec', {}).get('pricing')
        return None
    
    def estimate_cost(self, tokens: int, model: str = None) -> float:
        """Estimate DIEM cost using actual pricing"""
        if not model:
            model = "llama-3.3-70b"
        
        venice_model = self.resolve_model_name(model)
        pricing = self.get_model_pricing(venice_model)
        
        if not pricing:
            return (tokens / 1000000.0) * 0.5  # Fallback estimate
        
        # Assume 75% input, 25% output
        input_tokens = int(tokens * 0.75)
        output_tokens = int(tokens * 0.25)
        
        input_cost = (input_tokens / 1000000.0) * pricing.get('input', {}).get('diem', 0)
        output_cost = (output_tokens / 1000000.0) * pricing.get('output', {}).get('diem', 0)
        
        return input_cost + output_cost


class VeniceProvider(BaseLLMProvider):
    """Venice AI provider with DIEM tracking

    Token-Based Pricing Model:
    - Requires VVV token staking to earn daily DIEM allocation
    - 1 DIEM ≈ $631 USD (as of 2024)
    - Not a free service - requires capital investment in VVV tokens
    - Daily DIEM amount based on staked VVV quantity

    Features:
    - Privacy-focused, no data collection
    - Model discovery and compatibility mapping
    - Real-time pricing lookup
    - Automatic model aliasing
    - DIEM balance tracking
    """
    
    def __init__(self, config):
        """Initialize Venice provider
        
        Args:
            config: VeniceAIConfig with api_key, model settings, etc.
        """
        self.config = config
        self.api_key = config.api_key
        self.base_url = config.base_url
        self.timeout = config.timeout
        self.max_retries = config.max_retries
        
        # Initialize Venice API client
        self.venice_client = VeniceAPIClient(self.api_key, self.base_url)
        self._last_diem_status = None
    
    def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> LLMResponse:
        """Generate completion using Venice AI
        
        Args:
            prompt: User prompt
            system_prompt: System prompt
            **kwargs: Optional parameters (model, temperature, etc.)
            
        Returns:
            LLMResponse with generated content and DIEM cost
        """
        requested_model = kwargs.get("model", self.config.default_model)
        venice_model = self.venice_client.resolve_model_name(requested_model)
        
        # Check DIEM before request if enabled
        if getattr(self.config, 'check_diem_before_request', True):
            estimated_tokens = len(prompt.split()) * 1.3
            diem_status = self.venice_client.get_rate_limits()
            balances = diem_status.get('data', {}).get('balances', {})
            current_diem = balances.get('DIEM', 0)
            
            if current_diem < getattr(self.config, 'diem_critical_threshold', 0.1):
                if getattr(self.config, 'auto_fallback_on_low_diem', True):
                    raise RuntimeError(f"Insufficient DIEM ({current_diem:.2f} remaining)")
        
        # Prepare request
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": venice_model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 4096),
            "temperature": kwargs.get("temperature", 0.7)
        }
        
        try:
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
            usage = data.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", input_tokens + output_tokens)
            
            # Calculate DIEM cost using actual pricing
            pricing = self.venice_client.get_model_pricing(venice_model)
            if pricing:
                input_cost = (input_tokens / 1000000.0) * pricing.get('input', {}).get('diem', 0)
                output_cost = (output_tokens / 1000000.0) * pricing.get('output', {}).get('diem', 0)
                diem_cost = input_cost + output_cost
            else:
                diem_cost = self.venice_client.estimate_cost(total_tokens, venice_model)
            
            # Update status
            self._last_diem_status = self.venice_client.get_rate_limits()
            
            return LLMResponse(
                content=content,
                model=venice_model,
                tokens_used=total_tokens,
                cost=diem_cost,
                provider="venice",
                metadata={
                    "requested_model": requested_model,
                    "venice_model": venice_model,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "pricing": pricing
                }
            )
        
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise RuntimeError("Invalid Venice API key")
            else:
                raise RuntimeError(f"Venice API error: {e.response.text}")
        except Exception as e:
            raise RuntimeError(f"Venice request failed: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if Venice AI is accessible and has DIEM
        
        Returns:
            True if API is accessible and has remaining DIEM
        """
        if not self.config.enabled or not self.api_key:
            return False
        
        try:
            status = self.venice_client.get_rate_limits()
            balances = status.get('data', {}).get('balances', {})
            diem = balances.get('DIEM', 0)
            return diem > 0
        except Exception:
            return False
    
    def get_cost_per_token(self, model: str) -> float:
        """Get DIEM cost per token
        
        Args:
            model: Model name
            
        Returns:
            DIEM cost per token (varies by model)
        """
        # This is approximate - actual cost depends on model
        return 0.001
    
    def get_current_budget(self) -> Dict:
        """Get current DIEM budget status
        
        Returns:
            Dict with DIEM and USD balances
        """
        status = self.venice_client.get_rate_limits()
        data = status.get('data', {})
        balances = data.get('balances', {})

        return {
            'diem': balances.get('DIEM', 0),
            'usd': balances.get('USD', 0),
            'reset_time': data.get('nextEpochBegins'),
            'api_tier': data.get('apiTier', {}).get('id', 'unknown')
        }

    def get_available_models(self) -> List[ModelInfo]:
        """Get Venice models with real-time pricing and capabilities"""
        try:
            models_data = self.venice_client.get_models()
            result = []

            for model in models_data:
                model_id = model['id']
                spec = model.get('model_spec', {})
                pricing = spec.get('pricing', {})
                capabilities = spec.get('capabilities', {})

                result.append(ModelInfo(
                    id=model_id,
                    name=spec.get('description', model_id),
                    provider='venice',
                    capabilities={
                        'code': capabilities.get('optimizedForCode', False),
                        'reasoning': capabilities.get('supportsReasoning', False),
                        'vision': capabilities.get('supportsVision', False),
                        'function_calling': capabilities.get('supportsFunctionCalling', False),
                    },
                    context_window=spec.get('contextWindow', 4096),
                    input_cost_per_1k=pricing.get('input', {}).get('diem', 0) * 1000,
                    output_cost_per_1k=pricing.get('output', {}).get('diem', 0) * 1000,
                    currency='DIEM',
                    description=spec.get('description'),
                    parameter_count=spec.get('parameterCount')
                ))

            return result

        except Exception as e:
            return [ModelInfo(
                id=self.config.default_model,
                name=self.config.default_model,
                provider='venice',
                capabilities={'code': True, 'reasoning': True, 'vision': False, 'function_calling': False},
                context_window=8192,
                input_cost_per_1k=0.15,
                output_cost_per_1k=0.60,
                currency='DIEM'
            )]

