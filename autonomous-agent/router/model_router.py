#!/usr/bin/env python3
"""
Main Model Router for Autonomous Agent
Routes tasks to appropriate AI model providers based on task type, size, and rate limits.
"""

import logging
from typing import Dict, Optional, Any
from pathlib import Path

from .rate_limiter import RateLimiter
from .providers.groq_provider import GroqProvider
from .providers.venice_provider import VeniceProvider
from .providers.ollama_provider import OllamaProvider


class ModelRouter:
    """
    Routes tasks to the most cost-effective and appropriate model provider.
    
    Decision factors:
    - Task type and complexity
    - Prompt size (token count)
    - Provider rate limits and budgets
    - Cost optimization
    - Fallback strategies
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the ModelRouter with all available providers.
        
        Args:
            config_path: Optional path to configuration file
        """
        self.logger = logging.getLogger(__name__)
        
        # Initialize rate limiter
        self.rate_limiter = RateLimiter()
        
        # Load configuration if provided
        self.config = self._load_config(config_path)
        
        # Initialize providers
        self.providers = {}
        self._init_providers()
        
        # Task routing rules
        self.routing_rules = self._get_routing_rules()
        
        # Performance tracking
        self.request_history = []
        self.fallback_counts = {"groq": 0, "venice": 0, "ollama": 0}
        
        self.logger.info("ModelRouter initialized with providers: %s", list(self.providers.keys()))
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from file or use defaults."""
        default_config = {
            "preferences": {
                "max_prompt_tokens": 8000,  # Max tokens for Groq before switching to Venice
                "venice_budget_threshold": 0.1,  # Minimum DIEM balance to use Venice
                "token_buffer": 1000,  # Buffer to leave for responses
                "retry_attempts": 3,
                "fallback_strategy": "smart",  # Options: smart, cost, speed
            }
        }
        
        if config_path and Path(config_path).exists():
            try:
                import json
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                    # Merge with defaults
                    default_config.update(user_config)
            except Exception as e:
                self.logger.warning(f"Failed to load config from {config_path}: {e}. Using defaults.")
        
        return default_config
    
    def _get_routing_rules(self) -> Dict[str, Dict[str, Any]]:
        """Define routing rules for different task types."""
        return {
            "self_reflection": {
                "description": "Internal agent analysis and performance review",
                "preferred_provider": "ollama",
                "fallback_providers": [],
                "max_tokens": 2000,
                "temperature": 0.3,
                "priority": "low",
            },
            "critical_analysis": {
                "description": "High-stakes analysis, strategic decisions, structured arguments",
                "preferred_provider": "venice",
                "fallback_providers": ["groq"],
                "model_type": "reasoning",  # For Groq fallback
                "max_tokens": 4000,
                "temperature": 0.7,
                "priority": "high",
            },
            "code_generation": {
                "description": "Writing code, scripts, configuration files",
                "preferred_provider": "groq",
                "fallback_providers": ["venice"],
                "model_type": "tooling",  # Use Groq's tooling model
                "max_tokens": 3000,
                "temperature": 0.2,
                "priority": "medium",
            },
            "reasoning": {
                "description": "General reasoning, problem solving, analysis",
                "preferred_provider": "groq",
                "fallback_providers": ["venice", "ollama"],
                "model_type": "reasoning",  # Use Groq's reasoning model
                "max_tokens": 4000,
                "temperature": 0.7,
                "priority": "medium",
            },
            "documentation": {
                "description": "Writing documentation, explanations, summaries",
                "preferred_provider": "groq",
                "fallback_providers": ["venice"],
                "model_type": "reasoning",
                "max_tokens": 2000,
                "temperature": 0.5,
                "priority": "low",
            },
            "quick_answer": {
                "description": "Simple questions, quick lookups, small tasks",
                "preferred_provider": "groq",
                "fallback_providers": ["ollama"],
                "model_type": "reasoning",
                "max_tokens": 1000,
                "temperature": 0.7,
                "priority": "low",
            }
        }
    
    def _init_providers(self):
        """Initialize all available providers."""
        # Initialize Groq provider
        try:
            self.providers["groq"] = GroqProvider(rate_limiter=self.rate_limiter)
            self.logger.info("Groq provider initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Groq provider: {e}")
            self.providers["groq"] = None
        
        # Initialize Venice provider
        try:
            self.providers["venice"] = VeniceProvider(rate_limiter=self.rate_limiter)
            self.logger.info("Venice provider initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Venice provider: {e}")
            self.providers["venice"] = None
        
        # Initialize Ollama provider
        try:
            self.providers["ollama"] = OllamaProvider(rate_limiter=self.rate_limiter)
            self.logger.info("Ollama provider initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Ollama provider: {e}")
            self.providers["ollama"] = None
        
        # Check if we have at least one provider
        active_providers = [name for name, provider in self.providers.items() if provider is not None]
        if not active_providers:
            raise RuntimeError("No AI providers available. Check API keys and connections.")
        
        self.logger.info(f"Active providers: {active_providers}")
    
    def _classify_task(self, task_description: str) -> str:
        """
        Classify a task into one of the routing rule categories.
        
        Args:
            task_description: The task description
            
        Returns:
            Task category string
        """
        task_lower = task_description.lower()
        
        if any(keyword in task_lower for keyword in [
            "self reflection", "analyze performance", "internal analysis", 
            "performance review", "self assessment"
        ]):
            return "self_reflection"
        
        elif any(keyword in task_lower for keyword in [
            "critical analysis", "structured argument", "strategic decision",
            "partnership", "high stakes", "important analysis"
        ]):
            return "critical_analysis"
        
        elif any(keyword in task_lower for keyword in [
            "write code", "generate script", "create function", "implement",
            "program", "code", "script", "module", "class"
        ]):
            return "code_generation"
        
        elif any(keyword in task_lower for keyword in [
            "explain", "document", "summary", "summarize", 
            "documentation", "readme", "guide", "tutorial"
        ]):
            return "documentation"
        
        elif any(keyword in task_lower for keyword in [
            "quick", "simple", "lookup", "check", "verify",
            "what is", "how to", "tell me"
        ]):
            return "quick_answer"
        
        else:
            return "reasoning"  # Default category
    
    def _estimate_token_count(self, prompt: str) -> int:
        """
        Estimate token count for a prompt.
        
        Args:
            prompt: The prompt text
            
        Returns:
            Estimated token count
        """
        # Try each provider's tokenizer, use the first one that works
        for provider_name, provider in self.providers.items():
            if provider is not None:
                try:
                    return provider.count_tokens(prompt)
                except Exception as e:
                    self.logger.debug(f"Failed to count tokens with {provider_name}: {e}")
        
        # Fallback: rough estimation
        return len(prompt.split()) * 1.3
    
    def route_task(self, task_description: str) -> Dict[str, Any]:
        """
        Analyze a task and select the most appropriate model and provider.
        
        Args:
            task_description: The task description
            
        Returns:
            Dictionary with provider configuration
            
        Raises:
            RuntimeError: If no suitable provider is available
        """
        # Classify the task
        task_category = self._classify_task(task_description)
        rules = self.routing_rules.get(task_category, self.routing_rules["reasoning"])
        
        self.logger.debug(f"Task classified as '{task_category}': {task_description[:100]}...")
        
        # Estimate token count for this task
        estimated_tokens = self._estimate_token_count(task_description)
        self.logger.debug(f"Estimated token count: {estimated_tokens}")
        
        # Check if task is too large for preferred provider
        max_tokens = min(rules["max_tokens"], 4000)  # Cap at 4000
        total_estimated = estimated_tokens + max_tokens
        
        # Start with preferred provider
        preferred_provider = rules["preferred_provider"]
        
        # Special case: very large prompts
        if estimated_tokens > self.config["preferences"]["max_prompt_tokens"]:
            self.logger.info(f"Large prompt ({estimated_tokens} tokens), preferring Venice for capacity")
            preferred_provider = "venice"
        
        # Build provider chain to try
        provider_chain = []
        
        # Add preferred provider
        if self.providers.get(preferred_provider) is not None:
            provider_chain.append(preferred_provider)
        
        # Add fallback providers
        for fallback in rules.get("fallback_providers", []):
            if self.providers.get(fallback) is not None and fallback not in provider_chain:
                provider_chain.append(fallback)
        
        # Add any other available providers as last resort
        for provider_name, provider in self.providers.items():
            if provider is not None and provider_name not in provider_chain:
                provider_chain.append(provider_name)
        
        if not provider_chain:
            raise RuntimeError("No AI providers available")
        
        self.logger.debug(f"Provider chain: {provider_chain}")
        
        # Try each provider in order
        for provider_name in provider_chain:
            provider = self.providers[provider_name]
            
            # Check if provider can handle this task
            can_handle = False
            
            if provider_name == "groq":
                # For Groq, check if we should use tooling or reasoning model
                model_type = rules.get("model_type", "reasoning")
                can_handle = provider.can_handle(task_description, model_type=model_type)
            else:
                can_handle = provider.can_handle(task_description)
            
            if can_handle:
                # Prepare configuration
                config = {
                    "provider": provider_name,
                    "task_category": task_category,
                    "estimated_tokens": estimated_tokens,
                    "temperature": rules.get("temperature", 0.7),
                    "max_tokens": max_tokens,
                    "priority": rules.get("priority", "medium"),
                }
                
                # Add provider-specific configuration
                if provider_name == "groq":
                    config["model_type"] = rules.get("model_type", "reasoning")
                elif provider_name == "venice":
                    # Check budget threshold
                    if hasattr(provider, '_check_balance'):
                        # Get current balance if available
                        if provider.current_balance is not None:
                            if provider.current_balance < self.config["preferences"]["venice_budget_threshold"]:
                                self.logger.warning(
                                    f"Venice balance low ({provider.current_balance}), "
                                    f"below threshold ({self.config['preferences']['venice_budget_threshold']})"
                                )
                                # Skip Venice if balance is too low
                                continue
                
                self.logger.info(
                    f"Routing task to {provider_name.upper()} "
                    f"({task_category}, {estimated_tokens} tokens)"
                )
                
                return config
        
        # If we get here, no provider can handle the task
        self.logger.error("No provider can handle this task given current limits")
        
        # Last resort: try Ollama regardless of limits
        if self.providers.get("ollama") is not None:
            self.logger.warning("Using Ollama as last resort (no limits)")
            return {
                "provider": "ollama",
                "task_category": task_category,
                "estimated_tokens": estimated_tokens,
                "temperature": rules.get("temperature", 0.7),
                "max_tokens": min(max_tokens, 2000),  # Lower max for Ollama
                "priority": "low",
            }
        
        raise RuntimeError("No suitable provider available for this task")
    
    def execute_query(self, task_description: str) -> str:
        """
        Execute a query with the appropriate provider.
        
        This is the main entry point for external callers.
        
        Args:
            task_description: The task description or prompt
            
        Returns:
            Model response as string
            
        Raises:
            RuntimeError: If query cannot be executed
        """
        try:
            # Route the task
            routing_config = self.route_task(task_description)
            provider_name = routing_config["provider"]
            provider = self.providers[provider_name]
            
            # Prepare provider-specific parameters
            provider_params = {
                "prompt": task_description,
                "max_tokens": routing_config["max_tokens"],
                "temperature": routing_config["temperature"],
            }
            
            # Add Groq-specific parameters
            if provider_name == "groq":
                model_type = routing_config.get("model_type", "reasoning")
                provider_params["model_type"] = model_type
            
            # Execute query
            self.logger.info(
                f"Executing query with {provider_name.upper()} "
                f"(category: {routing_config['task_category']})"
            )
            
            response = provider.query(**provider_params)
            
            # Record successful request
            self.request_history.append({
                "timestamp": self._get_timestamp(),
                "provider": provider_name,
                "task_category": routing_config["task_category"],
                "estimated_tokens": routing_config["estimated_tokens"],
                "actual_tokens": None,  # Would need to be updated by provider
                "success": True,
            })
            
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to execute query: {e}")
            
            # Record failed request
            self.request_history.append({
                "timestamp": self._get_timestamp(),
                "provider": routing_config.get("provider", "unknown"),
                "task_category": routing_config.get("task_category", "unknown"),
                "estimated_tokens": routing_config.get("estimated_tokens", 0),
                "error": str(e),
                "success": False,
            })
            
            # Attempt fallback if primary provider failed
            if "provider" in routing_config:
                fallback_result = self._attempt_fallback(task_description, routing_config)
                if fallback_result:
                    return fallback_result
            
            raise RuntimeError(f"Query failed and no fallback available: {e}")
    
    def _attempt_fallback(self, task_description: str, failed_config: Dict[str, Any]) -> Optional[str]:
        """
        Attempt to execute query with a fallback provider.
        
        Args:
            task_description: The original task description
            failed_config: Configuration from failed attempt
            
        Returns:
            Response from fallback provider, or None if no fallback succeeds
        """
        task_category = failed_config.get("task_category", "reasoning")
        rules = self.routing_rules.get(task_category, self.routing_rules["reasoning"])
        
        # Get fallback providers from rules
        fallback_providers = rules.get("fallback_providers", [])
        
        # Remove the failed provider from chain
        failed_provider = failed_config["provider"]
        if failed_provider in fallback_providers:
            fallback_providers.remove(failed_provider)
        
        # Try each fallback provider
        for provider_name in fallback_providers:
            if self.providers.get(provider_name) is None:
                continue
            
            self.logger.warning(
                f"Attempting fallback to {provider_name.upper()} "
                f"after {failed_provider.upper()} failure"
            )
            
            try:
                provider = self.providers[provider_name]
                
                # Prepare parameters for fallback
                provider_params = {
                    "prompt": task_description,
                    "max_tokens": min(failed_config.get("max_tokens", 4000), 2000),  # Reduce for fallback
                    "temperature": failed_config.get("temperature", 0.7),
                }
                
                # Add Groq-specific parameters if applicable
                if provider_name == "groq":
                    provider_params["model_type"] = failed_config.get("model_type", "reasoning")
                
                response = provider.query(**provider_params)
                
                # Record fallback success
                self.fallback_counts[failed_provider] = self.fallback_counts.get(failed_provider, 0) + 1
                
                self.logger.info(f"Fallback to {provider_name.upper()} successful")
                return response
                
            except Exception as e:
                self.logger.warning(f"Fallback to {provider_name.upper()} also failed: {e}")
                continue
        
        return None
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about router performance.
        
        Returns:
            Dictionary with router statistics
        """
        total_requests = len(self.request_history)
        successful_requests = sum(1 for r in self.request_history if r.get("success", False))
        
        # Count requests by provider
        provider_counts = {}
        for request in self.request_history:
            provider = request.get("provider", "unknown")
            provider_counts[provider] = provider_counts.get(provider, 0) + 1
        
        # Count requests by category
        category_counts = {}
        for request in self.request_history:
            category = request.get("task_category", "unknown")
            category_counts[category] = category_counts.get(category, 0) + 1
        
        return {
            "total_requests": total_requests,
            "success_rate": (successful_requests / total_requests * 100) if total_requests > 0 else 0,
            "requests_by_provider": provider_counts,
            "requests_by_category": category_counts,
            "fallback_counts": self.fallback_counts,
            "active_providers": [name for name, provider in self.providers.items() if provider is not None],
        }
    
    def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status information for all providers.
        
        Returns:
            Dictionary with provider status information
        """
        status = {}
        
        for provider_name, provider in self.providers.items():
            if provider is None:
                status[provider_name] = {"available": False, "error": "Not initialized"}
                continue
            
            provider_status = {"available": True}
            
            # Add provider-specific status
            if provider_name == "groq":
                provider_status["available_tokens"] = provider.get_available_tokens()
                provider_status["models"] = list(provider.models.keys())
            elif provider_name == "venice":
                provider_status["balance"] = provider.current_balance
                provider_status["last_balance_check"] = provider.last_balance_check
                provider_status["available_tokens"] = provider.get_available_tokens()
            elif provider_name == "ollama":
                provider_status["endpoint"] = provider.endpoint
                provider_status["model"] = provider.model
            
            # Add common metrics
            provider_status["total_requests"] = provider.total_requests
            provider_status["total_cost"] = provider.total_cost
            
            status[provider_name] = provider_status
        
        return status


# Singleton instance for easy access
_router_instance = None

def get_model_router(config_path: Optional[str] = None) -> ModelRouter:
    """
    Get or create a singleton ModelRouter instance.
    
    Args:
        config_path: Optional path to configuration file
        
    Returns:
        ModelRouter instance
    """
    global _router_instance
    if _router_instance is None:
        _router_instance = ModelRouter(config_path)
    return _router_instance


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create router instance
    router = ModelRouter()
    
    # Example tasks
    tasks = [
        "Write a Python function to calculate Fibonacci sequence",
        "Analyze the performance of our autonomous agent system",
        "Create a detailed strategic plan for improving response accuracy",
        "Explain quantum computing in simple terms",
    ]
    
    # Test routing
    for task in tasks:
        print(f"\n{'='*60}")
        print(f"Task: {task}")
        print(f"{'='*60}")
        
        try:
            config = router.route_task(task)
            print(f"Routing decision: {config}")
        except Exception as e:
            print(f"Routing failed: {e}")
    
    # Get statistics
    stats = router.get_stats()
    print(f"\nRouter statistics: {stats}")
    
    # Get provider status
    status = router.get_provider_status()
    print(f"\nProvider status: {status}")