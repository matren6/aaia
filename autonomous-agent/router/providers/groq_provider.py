# /opt/autonomous-agent/router/providers/groq_provider.py
import os
import time
from tenacity import retry, stop_after_attempt, wait_exponential
import requests

from .base import BaseProvider

class GroqProvider(BaseProvider):
    """Groq API provider implementation."""
    
    def __init__(self, api_key: str = None, rate_limiter=None):
        super().__init__("groq")
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.rate_limiter = rate_limiter
        
        # Model configurations
        self.models = {
            "reasoning": {
                "name": "llama-3.1-70b-versatile",
                "cost_per_token": 0.00000059,
                "tpm_limit": 12000,  # Tokens per minute limit
                "max_context": 128000
            },
            "tooling": {
                "name": "llama3-groq-8b-8192-tool-use-preview",
                "cost_per_token": 0.00000019,
                "tpm_limit": 20000,  # Higher limit for smaller model
                "max_context": 8192
            }
        }
        
        # Initialize client
        try:
            from groq import Groq
            self.client = Groq(api_key=self.api_key)
            self.use_sdk = True
        except ImportError:
            self.use_sdk = False
            self.logger.warning("Groq SDK not available, using requests")
        
        # Load tokenizer if available
        try:
            import tiktoken
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except ImportError:
            self.tokenizer = None
            self.logger.warning("tiktoken not available, using fallback token counter")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken if available."""
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        return super().count_tokens(text)
    
    def can_handle(self, prompt: str, model_type: str = "reasoning") -> bool:
        """Check if Groq can handle this prompt (size limits)."""
        model_config = self.models.get(model_type, self.models["reasoning"])
        
        # Check prompt size
        prompt_tokens = self.count_tokens(prompt)
        if prompt_tokens > model_config["max_context"] - 1000:  # Leave room for response
            self.logger.warning(
                f"Prompt too large for Groq {model_type}: "
                f"{prompt_tokens}/{model_config['max_context']} tokens"
            )
            return False
        
        # Check rate limits
        estimated_tokens = prompt_tokens + 1000  # Estimate response size
        
        if not self.rate_limiter.check_rpm_limit(self.name):
            self.logger.warning("Groq RPM limit exceeded")
            return False
        
        if not self.rate_limiter.check_tpm_limit(self.name, estimated_tokens):
            self.logger.warning("Groq TPM limit would be exceeded")
            return False
        
        if not self.rate_limiter.check_daily_limits(self.name):
            self.logger.warning("Groq daily limits exceeded")
            return False
        
        return True
    
    def estimate_cost(self, prompt: str, max_tokens: int = 4000) -> float:
        """Estimate cost for this query."""
        prompt_tokens = self.count_tokens(prompt)
        
        # Use average cost for estimation
        avg_cost_per_token = 0.00000039  # Average of Groq models
        
        estimated_tokens = prompt_tokens + max_tokens
        return estimated_tokens * avg_cost_per_token
    
    def get_available_tokens(self) -> int:
        """Get available tokens in current minute window."""
        if self.name not in self.rate_limiter.tpm_windows:
            return self.models["reasoning"]["tpm_limit"]
        
        now = time.time()
        window_start = now - 60
        
        # Calculate used tokens in last minute
        used_tokens = sum(
            tokens for ts, tokens in self.rate_limiter.tpm_windows[self.name]
            if ts > window_start
        )
        
        # Use the most restrictive model's TPM limit
        tpm_limit = min(model["tpm_limit"] for model in self.models.values())
        return max(0, tpm_limit - used_tokens)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def query(self, prompt: str, max_tokens: int = 4000, temperature: float = 0.7, 
              model_type: str = "reasoning") -> str:
        """Execute a query with Groq."""
        model_config = self.models.get(model_type, self.models["reasoning"])
        
        # Final check before querying
        if not self.can_handle(prompt, model_type):
            raise Exception(f"Groq cannot handle this request due to limits")
        
        try:
            prompt_tokens = self.count_tokens(prompt)
            
            # Adjust max_tokens based on available capacity
            available_tokens = self.get_available_tokens()
            safe_max_tokens = min(max_tokens, available_tokens - prompt_tokens - 100)
            
            if safe_max_tokens < 100:
                raise Exception(
                    f"Insufficient token capacity: {available_tokens} available, "
                    f"{prompt_tokens} prompt tokens"
                )
            
            if self.use_sdk:
                # Using Groq SDK
                response = self.client.chat.completions.create(
                    model=model_config["name"],
                    messages=[
                        {"role": "system", "content": "You are a helpful AI assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=safe_max_tokens,
                    temperature=temperature,
                    stream=False
                )
                output_text = response.choices[0].message.content
            else:
                # Using requests
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": model_config["name"],
                    "messages": [
                        {"role": "system", "content": "You are a helpful AI assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": safe_max_tokens,
                    "temperature": temperature,
                    "stream": False
                }
                
                response = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()
                output_text = data["choices"][0]["message"]["content"]
            
            # Calculate actual cost
            output_tokens = self.count_tokens(output_text)
            total_tokens = prompt_tokens + output_tokens
            actual_cost = total_tokens * model_config["cost_per_token"]
            
            # Record the request
            self.record_request(actual_cost)
            self.rate_limiter.record_request(
                provider=self.name,
                tokens=total_tokens,
                cost=actual_cost
            )
            
            self.logger.info(
                f"Groq query completed ({model_type}). "
                f"Tokens: {prompt_tokens}+{output_tokens}={total_tokens}, "
                f"Cost: ${actual_cost:.6f}"
            )
            
            return output_text
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Groq API request failed: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in Groq query: {e}")
            raise