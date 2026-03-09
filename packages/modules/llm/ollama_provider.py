"""
Ollama Provider for AAIA LLM Integration

Handles local model inference via Ollama API.
Provides cost-effective, privacy-preserving model access with automatic model selection.

Features:
- Local model execution (100% free, no API costs)
- Automatic model discovery via /api/tags and /api/show
- Capability detection (vision from API, code/function-calling via heuristics)
- Speed-based optimization (picks fastest suitable model)
- Offline operation
"""

import subprocess
import requests
import time
from typing import Optional, List, Dict
from decimal import Decimal

from .base_provider import BaseLLMProvider, LLMResponse, ModelInfo
from .ollama_capabilities import (
    extract_capabilities_from_show,
    extract_context_window,
    calculate_speed_score,
    get_model_description
)


class OllamaAPIClient:
    """Client for Ollama API operations with intelligent caching"""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip('/')
        self._models_cache = None
        self._details_cache = {}  # {model_name: details}
        self._cache_timestamp = 0
        self._cache_ttl = 300  # 5 minutes

    def list_models(self, force_refresh: bool = False) -> List[Dict]:
        """Get list of installed models from /api/tags

        Args:
            force_refresh: Bypass cache and fetch fresh data

        Returns:
            List of model entries from Ollama

        Raises:
            requests.RequestException: If API call fails
        """
        if not force_refresh and self._is_cache_valid():
            return self._models_cache

        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            response.raise_for_status()

            data = response.json()
            self._models_cache = data.get('models', [])
            self._cache_timestamp = time.time()

            return self._models_cache

        except requests.RequestException as e:
            raise RuntimeError(f"Failed to list Ollama models: {e}")

    def get_model_details(self, model_name: str, use_cache: bool = True) -> Dict:
        """Get detailed info for specific model via /api/show

        Args:
            model_name: Model identifier (e.g., "llama3.2:3b")
            use_cache: Use cached details if available

        Returns:
            Full model details including capabilities and model_info

        Raises:
            requests.RequestException: If API call fails
        """
        if use_cache and model_name in self._details_cache:
            return self._details_cache[model_name]

        try:
            response = requests.post(
                f"{self.base_url}/api/show",
                json={"name": model_name},
                timeout=10
            )
            response.raise_for_status()

            details = response.json()
            self._details_cache[model_name] = details

            return details

        except requests.RequestException as e:
            raise RuntimeError(f"Failed to get details for {model_name}: {e}")

    def _is_cache_valid(self) -> bool:
        """Check if models cache is still valid"""
        if not self._models_cache:
            return False
        return (time.time() - self._cache_timestamp) < self._cache_ttl

    def clear_cache(self):
        """Clear all caches"""
        self._models_cache = None
        self._details_cache.clear()
        self._cache_timestamp = 0


class OllamaProvider(BaseLLMProvider):
    """Ollama provider for local model inference with automatic model selection

    Features:
    - 100% free local execution (no data sent to external servers)
    - Automatic model discovery and classification
    - Speed-based optimization (picks fastest suitable model)
    - Works offline
    - Fast inference

    Cost Model:
    - All models are free (local execution)
    - "Cost" = speed score (lower = faster)
    - Selection prioritizes smallest/fastest suitable model
    """

    def __init__(self, config):
        """Initialize Ollama provider

        Args:
            config: OllamaConfig with base_url, model, timeout, etc.
        """
        self.config = config
        self.base_url = config.base_url.rstrip('/')
        self.timeout = config.timeout
        self.max_retries = config.max_retries

        # Initialize Ollama API client
        self.ollama_client = OllamaAPIClient(self.base_url)
    
    def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> LLMResponse:
        """Generate completion using Ollama
        
        Args:
            prompt: User prompt
            system_prompt: System prompt
            **kwargs: Optional parameters (model, temperature, etc.)
            
        Returns:
            LLMResponse with generated content
        """
        model = kwargs.get("model", self.config.default_model)
        
        # Prepare request
        request = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        
        if system_prompt:
            request["system"] = system_prompt
        
        # Add optional parameters
        if "temperature" in kwargs:
            request["temperature"] = kwargs["temperature"]
        if "top_p" in kwargs:
            request["top_p"] = kwargs["top_p"]
        if "top_k" in kwargs:
            request["top_k"] = kwargs["top_k"]
        
        try:
            # Try using requests library (preferred)
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=request,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("response", "")
                
                # Estimate token count if not provided
                token_count = result.get("eval_count", len(prompt.split()) // 4)
                
                # Ollama is local, no cost
                cost = Decimal('0')
                
                return LLMResponse(
                    content=content,
                    model=model,
                    tokens_used=token_count,
                    cost=float(cost),
                    provider="ollama",
                    metadata={
                        "eval_count": result.get("eval_count", 0),
                        "prompt_eval_count": result.get("prompt_eval_count", 0),
                        "total_duration": result.get("total_duration", 0),
                        "load_duration": result.get("load_duration", 0),
                        "prompt_eval_duration": result.get("prompt_eval_duration", 0),
                        "eval_duration": result.get("eval_duration", 0)
                    }
                )
            else:
                raise Exception(f"Ollama API error: {response.text}")
        
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                f"Cannot connect to Ollama at {self.base_url}. "
                f"Is Ollama running? Start with: ollama serve"
            )
        except requests.exceptions.Timeout:
            raise RuntimeError(f"Ollama request timed out (timeout: {self.timeout}s)")
        except Exception as e:
            # Fallback to subprocess if requests fails
            try:
                cmd = ["ollama", "run", model, prompt]
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    input=prompt
                )
                
                if result.returncode == 0:
                    content = result.stdout
                    token_count = len(prompt.split()) // 4
                    
                    return LLMResponse(
                        content=content,
                        model=model,
                        tokens_used=token_count,
                        cost=0.0,
                        provider="ollama",
                        metadata={"method": "subprocess"}
                    )
                else:
                    raise Exception(f"Ollama error: {result.stderr}")
            except Exception as fallback_error:
                raise RuntimeError(f"Ollama inference failed: {str(e)} / {str(fallback_error)}")
    
    def is_available(self) -> bool:
        """Check if Ollama is running and accessible
        
        Returns:
            True if Ollama API is reachable
        """
        if not self.config.enabled:
            return False
        
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def get_cost_per_token(self, model: str) -> float:
        """Get cost per token for Ollama models
        
        Args:
            model: Model name
            
        Returns:
            0.0 (Ollama is free, runs locally)
        """
        return 0.0
    
    def get_available_models(self) -> List[ModelInfo]:
        """Get installed Ollama models with capabilities

        Discovery process:
        1. List models via /api/tags
        2. Get details for each via /api/show
        3. Extract capabilities (using native API data)
        4. Calculate speed scores
        5. Return sorted by speed (fastest first)

        Returns:
            List of ModelInfo objects sorted by speed (fastest first)
        """
        try:
            # Get list of installed models
            models_list = self.ollama_client.list_models()
            result = []

            for model_entry in models_list:
                model_name = model_entry['name']

                # Get detailed info via /api/show
                try:
                    show_data = self.ollama_client.get_model_details(model_name)
                except Exception as e:
                    print(f"Warning: Could not get details for {model_name}: {e}")
                    continue

                # Extract capabilities using Ollama's native data
                capabilities = extract_capabilities_from_show(show_data)

                # Extract exact context window
                context_window = extract_context_window(show_data)

                # Calculate speed score (lower = faster)
                details = show_data.get('details', {})
                speed_score = calculate_speed_score(details)

                # Generate description
                description = get_model_description(details)

                # Create ModelInfo
                result.append(ModelInfo(
                    id=model_name,
                    name=model_name,
                    provider='ollama',
                    capabilities=capabilities,
                    context_window=context_window,
                    input_cost_per_1k=speed_score,  # Use speed as "cost"
                    output_cost_per_1k=0.0,         # Free (local)
                    currency='SPEED_SCORE',
                    description=description,
                    parameter_count=details.get('parameter_size', 'Unknown')
                ))

            # Sort by speed (fastest first)
            result.sort(key=lambda m: m.input_cost_per_1k)

            return result

        except Exception as e:
            print(f"Warning: Ollama model discovery failed: {e}")
            # Fallback to default model
            return [self._get_fallback_model()]

    def _get_fallback_model(self) -> ModelInfo:
        """Get fallback ModelInfo when discovery fails"""
        return ModelInfo(
            id=self.config.default_model,
            name=f'Ollama {self.config.default_model}',
            provider='ollama',
            capabilities={
                'code': True,
                'reasoning': True,
                'vision': False,
                'function_calling': False
            },
            context_window=4096,
            input_cost_per_1k=50.0,  # Medium speed score
            output_cost_per_1k=0.0,
            currency='SPEED_SCORE',
            description='Fallback model (discovery failed)',
            parameter_count='Unknown'
        )
