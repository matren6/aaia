# /opt/autonomous-agent/router/providers/ollama_provider.py
import os
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from .base import BaseProvider


class OllamaProvider(BaseProvider):
    """Ollama local provider implementation."""
    
    def __init__(self, rate_limiter=None):
        super().__init__("ollama")
        self.rate_limiter = rate_limiter
        
        # Ollama configuration
        self.endpoint = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
        
        # Ollama has no cost
        self.cost_per_token = 0.0
        
        # Default configuration
        self.default_max_tokens = 2000
        self.default_temperature = 0.7
        
        # Health check
        self._check_health()
        
        self.logger.info(f"Ollama provider initialized with model: {self.model}")
    
    def _check_health(self):
        """Check if Ollama is available."""
        try:
            response = requests.get(f"{self.endpoint}/api/tags", timeout=5)
            if response.status_code == 200:
                self.logger.info("Ollama is available")
                return True
            else:
                self.logger.warning(f"Ollama returned status {response.status_code}")
                return False
        except Exception as e:
            self.logger.warning(f"Ollama health check failed: {e}")
            return False
    
    def count_tokens(self, text: str) -> int:
        """Count tokens for Ollama (approximate)."""
        # Ollama doesn't have a tokenizer API, so we use a rough estimate
        return super().count_tokens(text)
    
    def can_handle(self, prompt: str) -> bool:
        """Check if Ollama can handle this prompt."""
        # Ollama has no rate limits or budgets
        # But we should check if the prompt is too large
        
        prompt_tokens = self.count_tokens(prompt)
        if prompt_tokens > 32000:  # Conservative limit for local models
            self.logger.warning(
                f"Prompt too large for Ollama: {prompt_tokens} tokens"
            )
            return False
        
        # Check if Ollama is reachable
        if not self._check_health():
            self.logger.warning("Ollama is not available")
            return False
        
        return True
    
    def estimate_cost(self, prompt: str, max_tokens: int = 2000) -> float:
        """Ollama is free."""
        return 0.0
    
    def get_available_tokens(self) -> int:
        """Ollama has effectively unlimited tokens."""
        return 1000000  # Arbitrarily large number
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def query(self, prompt: str, max_tokens: int = None, temperature: float = None) -> str:
        """Execute a query with Ollama."""
        # Use defaults if not specified
        if max_tokens is None:
            max_tokens = self.default_max_tokens
        if temperature is None:
            temperature = self.default_temperature
        
        # Ollama doesn't support max_tokens parameter directly
        # We'll use num_predict instead
        num_predict = min(max_tokens, 4000)  # Cap at 4000 for safety
        
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": num_predict,
                    "temperature": temperature,
                    "top_p": 0.9,
                    "repeat_penalty": 1.1
                }
            }
            
            response = requests.post(
                f"{self.endpoint}/api/generate",
                json=payload,
                timeout=60  # Longer timeout for local inference
            )
            response.raise_for_status()
            
            result = response.json()
            
            if "response" not in result:
                raise ValueError(f"Ollama response missing 'response' field: {result}")
            
            output_text = result["response"]
            
            # Calculate token usage from response if available
            prompt_tokens = result.get("prompt_eval_count", self.count_tokens(prompt))
            output_tokens = result.get("eval_count", self.count_tokens(output_text))
            total_tokens = prompt_tokens + output_tokens
            
            # Record the request (cost is 0)
            self.record_request(0.0)
            if self.rate_limiter:
                self.rate_limiter.record_request(
                    provider=self.name,
                    tokens=total_tokens,
                    cost=0.0
                )
            
            self.logger.info(
                f"Ollama query completed. "
                f"Tokens: {prompt_tokens}+{output_tokens}={total_tokens}"
            )
            
            return output_text
            
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Ollama connection error: {e}")
            raise Exception(f"Ollama is not available: {e}")
        except requests.exceptions.Timeout as e:
            self.logger.error(f"Ollama request timeout: {e}")
            raise Exception(f"Ollama request timed out: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error in Ollama query: {e}")
            raise