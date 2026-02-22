# /opt/autonomous-agent/router/providers/venice_provider.py
import os
import time
from tenacity import retry, stop_after_attempt, wait_exponential
import requests
from openai import OpenAI

from .base import BaseProvider

class VeniceProvider(BaseProvider):
    """Venice API provider implementation."""
    
    def __init__(self, api_key: str = None, rate_limiter=None):
        super().__init__("venice")
        self.api_key = api_key or os.getenv("VENICE_API_KEY")
        self.rate_limiter = rate_limiter
        
        # Venice-specific configuration
        self.model_config = {
            "name": "deepseek-v3.2",
            "cost_per_input_token": 0.0000004,   # $0.40 per 1M tokens
            "cost_per_output_token": 0.000001,    # $1.00 per 1M tokens
            "max_context": 128000,
            "daily_budget": 0.49  # $0.49 daily DIEM allowance
        }
        
        # Initialize client
        try:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.venice.ai/v1"
            )
            self.use_sdk = True
        except ImportError:
            self.use_sdk = False
            self.logger.warning("OpenAI SDK not available for Venice")
        
        # Balance cache
        self.last_balance_check = None
        self.current_balance = None
        
        # Load tokenizer if available
        try:
            import tiktoken
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except ImportError:
            self.tokenizer = None
    
    def count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken if available."""
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        return super().count_tokens(text)
    
    def _check_balance(self, estimated_cost: float = 0.02) -> bool:
        """Check Venice DIEM balance via API."""
        # Cache balance for 5 minutes
        if (self.last_balance_check is not None and 
            time.time() - self.last_balance_check < 300):
            if self.current_balance is not None:
                return self.current_balance >= estimated_cost
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                "https://api.venice.ai/api/v1/api_keys/rate_limits",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            balances = data.get('data', {}).get('balances', {})
            diem_balance = balances.get('DIEM', 0)
            
            self.current_balance = diem_balance
            self.last_balance_check = time.time()
            
            self.logger.info(f"Venice DIEM balance: {diem_balance}")
            
            return diem_balance >= estimated_cost
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch Venice balance: {e}")
            return False
    
    def can_handle(self, prompt: str) -> bool:
        """Check if Venice can handle this prompt."""
        # Check prompt size
        prompt_tokens = self.count_tokens(prompt)
        if prompt_tokens > self.model_config["max_context"] - 1000:
            self.logger.warning(
                f"Prompt too large for Venice: "
                f"{prompt_tokens}/{self.model_config['max_context']} tokens"
            )
            return False
        
        # Check rate limits
        if not self.rate_limiter.check_rpm_limit(self.name):
            self.logger.warning("Venice RPM limit exceeded")
            return False
        
        # Check daily budget
        estimated_cost = self.estimate_cost(prompt, max_tokens=4000)
        if not self.rate_limiter.check_daily_limits(self.name, estimated_cost):
            self.logger.warning("Venice daily budget would be exceeded")
            return False
        
        # Check actual balance
        if not self._check_balance(estimated_cost):
            self.logger.warning("Venice balance insufficient")
            return False
        
        return True
    
    def estimate_cost(self, prompt: str, max_tokens: int = 4000) -> float:
        """Estimate cost for this query."""
        prompt_tokens = self.count_tokens(prompt)
        
        input_cost = prompt_tokens * self.model_config["cost_per_input_token"]
        output_cost = max_tokens * self.model_config["cost_per_output_token"]
        
        return input_cost + output_cost
    
    def get_available_tokens(self) -> int:
        """Venice doesn't have TPM limits, but has budget limits."""
        # Estimate tokens based on remaining budget
        if self.current_balance is None:
            return 1000000  # Large number if we don't know
        
        # Convert DIEM balance to approximate tokens
        # Using average cost per token
        avg_cost_per_token = (self.model_config["cost_per_input_token"] + 
                             self.model_config["cost_per_output_token"]) / 2
        
        if avg_cost_per_token <= 0:
            return 1000000
        
        return int(self.current_balance / avg_cost_per_token)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def query(self, prompt: str, max_tokens: int = 4000, temperature: float = 0.7) -> str:
        """Execute a query with Venice."""
        # Final check before querying
        if not self.can_handle(prompt):
            raise Exception("Venice cannot handle this request due to limits or budget")
        
        try:
            prompt_tokens = self.count_tokens(prompt)
            estimated_cost = self.estimate_cost(prompt, max_tokens)
            
            if self.use_sdk:
                response = self.client.chat.completions.create(
                    model=self.model_config["name"],
                    messages=[
                        {"role": "system", "content": "You are a helpful AI assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stream=False
                )
                output_text = response.choices[0].message.content
            else:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": self.model_config["name"],
                    "messages": [
                        {"role": "system", "content": "You are a helpful AI assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "stream": False
                }
                
                response = requests.post(
                    "https://api.venice.ai/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=60
                )
                response.raise_for_status()
                data = response.json()
                output_text = data["choices"][0]["message"]["content"]
            
            # Calculate actual cost
            output_tokens = self.count_tokens(output_text)
            actual_cost = (
                prompt_tokens * self.model_config["cost_per_input_token"] +
                output_tokens * self.model_config["cost_per_output_token"]
            )
            
            # Record the request
            self.record_request(actual_cost)
            self.rate_limiter.record_request(
                provider=self.name,
                tokens=prompt_tokens + output_tokens,
                cost=actual_cost
            )
            
            self.logger.info(
                f"Venice query completed. "
                f"Tokens: {prompt_tokens}+{output_tokens}={prompt_tokens + output_tokens}, "
                f"Cost: ${actual_cost:.6f}, "
                f"Remaining DIEM: {self.current_balance - actual_cost if self.current_balance else 'unknown'}"
            )
            
            return output_text
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                self.logger.warning("Venice rate limit exceeded")
                raise
            elif e.response.status_code == 402:
                self.logger.error("Venice payment required - budget may be exhausted")
                # Clear cache to force re-check
                self.current_balance = None
                raise
            else:
                self.logger.error(f"Venice API HTTP error: {e.response.status_code}")
                raise
        except Exception as e:
            self.logger.error(f"Unexpected error in Venice query: {e}")
            raise