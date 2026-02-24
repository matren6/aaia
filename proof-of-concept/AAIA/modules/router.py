"""
Router Module - Intelligent Model Selection and Routing

PURPOSE:
The Router is responsible for selecting the appropriate AI model for each task
and managing the interaction with those models. It implements cost-benefit analysis
to choose between different models based on task complexity and cost.

PROBLEM SOLVED:
Different tasks require different AI capabilities:
- Simple tasks shouldn't use expensive models (waste of resources)
- Complex reasoning tasks need more capable models
- Coding tasks benefit from code-specialized models
- Without routing, the system would either overspend on simple tasks or produce
  poor results on complex tasks

KEY RESPONSIBILITIES:
1. Maintain registry of available models with their capabilities and costs
2. Route requests to appropriate model based on task type and complexity
3. Execute model calls via Ollama API
4. Calculate and track inference costs
5. Handle fallback when preferred model unavailable
6. Optimize for cost-performance tradeoff

PROBLEM IT SOLVES:
- Cost optimization: Use cheap models for simple tasks
- Capability matching: Use specialized models for specialized tasks
- Resource management: Track token usage and costs
- Abstraction: Other modules don't need to know model details

DEPENDENCIES: EconomicManager (for cost tracking)
OUTPUTS: Model responses for reasoning, analysis, code generation
"""

import subprocess
import json
from decimal import Decimal
from typing import Dict, Tuple
from .economics import EconomicManager

class ModelRouter:
    def __init__(self, economic_manager: EconomicManager):
        self.economic_manager = economic_manager
        self.available_models = {
            "local:llama2": {
                "capabilities": ["reasoning", "general"],
                "cost_per_token": Decimal('0.000001'),
                "max_tokens": 4096
            },
            "local:mistral": {
                "capabilities": ["reasoning", "coding"],
                "cost_per_token": Decimal('0.000001'),
                "max_tokens": 8192
            },
            "local:codellama": {
                "capabilities": ["coding"],
                "cost_per_token": Decimal('0.000001'),
                "max_tokens": 4096
            }
        }
        
    def route_request(self, task_type: str, complexity: str = "medium") -> Tuple[str, Dict]:
        """Route task to appropriate model based on cost-benefit analysis"""
        # Simple routing logic - can be expanded
        if "code" in task_type.lower():
            return "local:codellama", self.available_models["local:codellama"]
        elif "reason" in task_type.lower():
            return "local:mistral", self.available_models["local:mistral"]
        else:
            return "local:llama2", self.available_models["local:llama2"]
            
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
            result = subprocess.run(cmd, capture_output=True, text=True, input=prompt)
            
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