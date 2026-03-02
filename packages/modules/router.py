import subprocess
import json
from decimal import Decimal
from typing import Dict, Tuple
from .economics import EconomicManager

# Import PromptManager
try:
    from prompts import get_prompt_manager
except ImportError:
    get_prompt_manager = None


class ModelRouter:
    def __init__(self, economic_manager: EconomicManager, event_bus=None):
        """
        Initialize the Model Router.
        
        Args:
            economic_manager: EconomicManager for cost tracking
            event_bus: Optional EventBus for publishing events
        """
        self.economic_manager = economic_manager
        self.event_bus = event_bus
        
        # Initialize PromptManager
        self.prompt_manager = None
        if get_prompt_manager:
            try:
                self.prompt_manager = get_prompt_manager()
            except Exception as e:
                print(f"Warning: Failed to initialize PromptManager: {e}")

        # Load configuration
        try:
            from modules.settings import get_config
            config = get_config()
            self.config = config.llm
        except Exception:
            # Use defaults
            class DefaultLLMConfig:
                provider = "ollama"
                model = "phi3"
                base_url = "http://localhost:11434"
                timeout = 120
                max_retries = 3
            self.config = DefaultLLMConfig()
        
        # Load model configurations from config or use defaults
        self.available_models = {
            # Add configured model
            f"local:{self.config.model}": {
                "capabilities": ["reasoning", "general", "coding"],
                "cost_per_token": Decimal('0.000001'),
                "max_tokens": self.config.max_tokens if hasattr(self.config, 'max_tokens') else 4096
            }
        }
        
        # Use configured model as default
        self.default_model = f"local:{self.config.model}"
        
    def route_request(self, task_type: str, complexity: str = "medium") -> Tuple[str, Dict]:
        """
        Route task to appropriate model based on cost-benefit analysis.
        
        Args:
            task_type: Type of task (coding, reasoning, general, etc.)
            complexity: Complexity level (low, medium, high)
            
        Returns:
            Tuple of (model_name, model_info)
        """
        # Check if there's a prompt with model preferences for this task
        model_preferences = {}

        if self.prompt_manager:
            try:
                # Try to find prompts that match the task type
                prompts = self.prompt_manager.list_prompts()
                for prompt_info in prompts:
                    raw_prompt = self.prompt_manager.get_prompt_raw(prompt_info["name"])
                    prefs = raw_prompt.get("model_preferences", {})
                    if prefs.get("task_type", "").lower() == task_type.lower():
                        model_preferences = prefs
                        break
            except Exception as e:
                print(f"Warning: Error getting prompt preferences: {e}")

        # Use complexity from prompt preferences if available
        if model_preferences.get("complexity"):
            complexity = model_preferences.get("complexity", complexity)

        # Simple routing logic - can be expanded
        if "code" in task_type.lower():
            # Prefer codellama for coding tasks
            if "local:codellama" in self.available_models:
                return "local:codellama", self.available_models["local:codellama"]
        elif "reason" in task_type.lower():
            # Prefer mistral for reasoning tasks
            if "local:mistral" in self.available_models:
                return "local:mistral", self.available_models["local:mistral"]
        
        # Default to configured model
        return self.default_model, self.available_models.get(self.default_model, self.available_models["local:llama2"])
            
    def call_model(self, model_name: str, prompt: str, system_prompt: str = "") -> str:
        """Call Ollama model"""
        if not model_name.startswith("local:"):
            raise ValueError("Only local models supported in PoC")
            
        model = model_name.replace("local:", "")
        
        # Prepare request to Ollama
        request = {
            "model": model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False
        }
        
        try:
            # Using Ollama's API via curl (could use ollama Python package)
            import requests
            response = requests.post(
                "http://localhost:11434/api/generate",
                json=request,
                timeout=300
                )
                
            if response.status_code == 200:
                result = response.json()
                token_count = result.get("eval_count", len(prompt) // 4)
                
                # Calculate and log cost
                model_info = self.available_models[model_name]
                cost = self.economic_manager.calculate_cost(model_name, token_count)
                self.economic_manager.log_transaction(
                    f"Model inference: {model_name}",
                    -cost,  # Negative for expense
                    "inference"
                )
                
                return result["response"]
            else:
                raise Exception(f"Ollama API error: {response.text}")
                
        except ImportError:
            # Fallback to subprocess if requests not available
            cmd = ["ollama", "run", model, prompt]
            result = subprocess.run(cmd, capture_output=True, text=True, input=prompt, check=False)
            
            if result.returncode == 0:
                # Estimate token count (rough approximation)
                token_count = len(prompt.split()) * 1.3
                cost = self.economic_manager.calculate_cost(model_name, int(token_count))
                self.economic_manager.log_transaction(
                    f"Model inference: {model_name}",
                    -cost,
                    "inference"
                )
                
                return result.stdout
            else:
                raise Exception(f"Ollama error: {result.stderr}")

