import subprocess
import json
from decimal import Decimal
from typing import Dict, Tuple, Optional, Any
from datetime import datetime
from .economics import EconomicManager
from modules.container import DependencyError, get_container
from modules.bus import Event, EventType
import uuid
import time


class ModelRouter:
    def __init__(self, economic_manager: EconomicManager, event_bus=None, prompt_manager=None, config=None, marginal_analyzer=None):
        """
        Initialize the Model Router with multi-provider support.

        Args:
            economic_manager: EconomicManager for cost tracking
            event_bus: Optional EventBus for publishing events
            prompt_manager: Optional PromptManager for prompt preferences
            config: Optional SystemConfig (if None, loads from env)
            marginal_analyzer: Optional MarginalAnalyzer for Phase 2
        """
        self.economic_manager = economic_manager
        self.event_bus = event_bus
        self.prompt_manager = prompt_manager
        self.marginal_analyzer = marginal_analyzer


        # Load configuration
        try:
            if config is None:
                from modules.settings import SystemConfig
                config = SystemConfig.from_env()
            self.config = config
            self.llm_config = config.llm
        except Exception as e:
            # Fallback to basic config
            print(f"Warning: Failed to load config: {e}, using defaults")
            class DefaultLLMConfig:
                default_provider = "ollama"
                fallback_provider = None
                class ollama:
                    enabled = True
                    base_url = "http://localhost:11434"
                    default_model = "phi3"
                    timeout = 120
                    max_retries = 3
            self.llm_config = DefaultLLMConfig()

        # Initialize provider factory
        try:
            from modules.llm.provider_factory import ProviderFactory
            self.provider_factory = ProviderFactory(self.llm_config)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize ProviderFactory: {e}")

        # Cache for provider health status
        self._provider_health = {}

        # Legacy compatibility - map old model names to new system
        self.available_models = self._build_legacy_models()

    def _build_legacy_models(self) -> Dict:
        """Build legacy model map for backward compatibility"""
        models = {}
        # Map new providers to old local: format
        available = self.provider_factory.list_available_providers()

        for provider in available:
            provider_instance = self.provider_factory.get_provider(provider)
            if provider == "ollama":
                model = getattr(self.llm_config.ollama, 'default_model', 'phi3')
                models[f"local:{model}"] = {
                    "capabilities": ["reasoning", "general", "coding"],
                    "cost_per_token": Decimal('0.000001'),
                    "max_tokens": 4096,
                    "provider": "ollama"
                }

        return models

    def select_provider(self, task_type: str = "general", 
                       complexity: str = "medium",
                       preferred_provider: Optional[str] = None,
                       use_marginal_analysis: bool = True) -> str:
        """Select appropriate provider based on task requirements

        Phase 2: Uses marginal analysis for Austrian Economic optimization

        Args:
            task_type: Type of task (general, code, analysis, etc.)
            complexity: Complexity level (low, medium, high)
            preferred_provider: Explicit provider override
            use_marginal_analysis: Use Phase 2 marginal analysis (if available)

        Returns:
            Provider name to use

        Selection Priority:
        1. Explicit preferred_provider
        2. Marginal analysis (Phase 2) - if enabled and available
        3. Prompt template preferences (from PromptManager)
        4. Task-based routing (complex → paid, simple → free)
        5. Default provider from config
        """
        # 1. Explicit override
        if preferred_provider:
            return preferred_provider

        # 2. Phase 2: Use marginal analysis if available
        if use_marginal_analysis and self.marginal_analyzer:
            try:
                available = self.provider_factory.list_available_providers()
                if available:
                    selected, analysis = self.marginal_analyzer.analyze(
                        available_providers=available,
                        task_type=task_type,
                        complexity=complexity,
                        expected_tokens=1000,  # Default estimate
                        minimum_quality_threshold=0.7
                    )
                    return selected
            except Exception:
                pass  # Fall through to next method

        # 3. Check prompt preferences
        if self.prompt_manager:
            preferences = self._get_prompt_preferences(task_type)
            if preferences and 'provider' in preferences:
                return preferences['provider']

        # 4. Smart routing based on complexity
        if complexity == "high":
            # Complex tasks → use powerful providers
            available = self.provider_factory.list_available_providers()
            # Prefer: openai > azure > venice > github > ollama
            for provider in ['openai', 'azure', 'venice', 'github']:
                if provider in available:
                    return provider

        elif complexity == "low":
            # Simple tasks → use free/local providers
            available = self.provider_factory.list_available_providers()
            # Prefer: ollama > github > venice > openai
            for provider in ['ollama', 'github', 'venice']:
                if provider in available:
                    return provider

        # 5. Default provider
        return self.llm_config.default_provider

    def _get_prompt_preferences(self, task_type: str) -> Optional[Dict]:
        """Get prompt preferences from PromptManager

        Args:
            task_type: Task type to look up

        Returns:
            Dict with preferences or None
        """
        if not self.prompt_manager:
            return None

        try:
            # Try to find prompts that match the task type
            prompts = self.prompt_manager.list_prompts()
            for prompt_info in prompts:
                raw_prompt = self.prompt_manager.get_prompt_raw(prompt_info["name"])
                prefs = raw_prompt.get("model_preferences", {})
                if prefs.get("task_type", "").lower() == task_type.lower():
                    return prefs
        except Exception:
            pass

        return None

    def route_request(self, task_type: str, complexity: str = "medium",
                     preferred_provider: Optional[str] = None):
        """Route request to appropriate provider

        Args:
            task_type: Type of task
            complexity: Complexity level
            preferred_provider: Preferred provider

        Returns:
            BaseLLMProvider instance
        """
        provider_name = self.select_provider(task_type, complexity, preferred_provider)
        return self.provider_factory.get_provider(provider_name)

    def _track_cost(self, response) -> None:
        """Track inference cost in EconomicManager

        Args:
            response: LLMResponse with cost information
        """
        if not self.economic_manager:
            return

        description = f"LLM Inference: {response.provider}/{response.model}"

        # Convert cost to Decimal
        cost_decimal = Decimal(str(response.cost))

        self.economic_manager.log_transaction(
            description=description,
            amount=-cost_decimal,  # Negative = expense
            category="inference",
            metadata={
                "provider": response.provider,
                "model": response.model,
                "tokens": response.tokens_used,
                "cost_per_token": response.cost / response.tokens_used if response.tokens_used > 0 else 0
            } if hasattr(self.economic_manager.log_transaction, '__code__') and 'metadata' in self.economic_manager.log_transaction.__code__.co_varnames else None
        )

    def _emit_inference_event(self, response) -> None:
        """Emit MODEL_INFERENCE event via EventBus

        Args:
            response: LLMResponse with inference details
        """
        if not self.event_bus:
            return

        try:
            self.event_bus.publish(Event(
                type=EventType.MODEL_INFERENCE,
                data={
                    "provider": getattr(response, 'provider', None),
                    "model": getattr(response, 'model', None),
                    "tokens_used": getattr(response, 'tokens_used', None),
                    "cost": getattr(response, 'cost', None),
                    "timestamp": getattr(response, 'timestamp', datetime.now()).isoformat() if hasattr(getattr(response, 'timestamp', None), 'isoformat') else str(getattr(response, 'timestamp', datetime.now())),
                    "success": True
                },
                source='ModelRouter'
            ))
        except Exception as e:
            print(f"Warning: Failed to publish event: {e}")

    def _update_provider_health(self, provider_name: str, success: bool, error: str = None) -> None:
        """Update provider health status

        Args:
            provider_name: Name of provider
            success: Whether request succeeded
            error: Error message if failed
        """
        if provider_name not in self._provider_health:
            self._provider_health[provider_name] = {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'last_success': None,
                'last_failure': None,
                'last_error': None
            }

        health = self._provider_health[provider_name]
        health['total_requests'] += 1

        if success:
            health['successful_requests'] += 1
            health['last_success'] = datetime.now()
        else:
            health['failed_requests'] += 1
            health['last_failure'] = datetime.now()
            health['last_error'] = error

    def get_provider_health(self, provider_name: Optional[str] = None) -> Dict:
        """Get health status for provider(s)

        Args:
            provider_name: Specific provider or None for all

        Returns:
            Dict with health metrics
        """
        if provider_name:
            return self._provider_health.get(provider_name, {})
        return self._provider_health.copy()

    def select_model(self, 
                    provider_name: str, 
                    task_type: Optional[str] = None,
                    complexity: str = "medium",
                    max_cost: Optional[float] = None) -> str:
        """Select optimal model within provider based on economic criteria

        Args:
            provider_name: Provider to select model from
            task_type: Type of task (code, reasoning, vision, general)
            complexity: Task complexity (low, medium, high)
            max_cost: Maximum cost per 1K tokens (optional budget constraint)

        Returns:
            Model ID to use
        """
        provider = self.provider_factory.get_provider(provider_name)

        try:
            model_id = provider.select_optimal_model(task_type, complexity, max_cost)

            # Log selection for transparency
            if self.event_bus:
                try:
                    self.event_bus.publish(Event(
                        type=EventType.MODEL_INFERENCE,
                        data={
                            'action': 'model_selected',
                            'provider': provider_name,
                            'model': model_id,
                            'task_type': task_type,
                            'complexity': complexity,
                            'max_cost': max_cost
                        },
                        source='ModelRouter'
                    ))
                except Exception:
                    pass

            return model_id

        except Exception as e:
            print(f"Warning: Model selection failed for {provider_name}: {e}")
            return provider.config.default_model

    def get_model_selection_stats(self) -> Dict[str, Any]:
        """Get statistics about model selection patterns

        Returns:
            Dict with selection analytics
        """
        if not self.event_bus:
            return {}

        from .bus import EventType
        events = self.event_bus.get_history(EventType.MODEL_INFERENCE)
        selection_events = [e for e in events if e.data.get('action') == 'model_selected']

        if not selection_events:
            return {'total_selections': 0}

        model_counts = {}
        complexity_distribution = {'low': 0, 'medium': 0, 'high': 0}

        for event in selection_events:
            model = event.data.get('model')
            complexity = event.data.get('complexity', 'medium')
            model_counts[model] = model_counts.get(model, 0) + 1
            complexity_distribution[complexity] = complexity_distribution.get(complexity, 0) + 1

        return {
            'total_selections': len(selection_events),
            'model_distribution': model_counts,
            'complexity_distribution': complexity_distribution,
            'most_used_model': max(model_counts.items(), key=lambda x: x[1])[0] if model_counts else None
        }

    def call_model(self, prompt: str, system_prompt: str = "",
                  task_type: str = "general", 
                  complexity: str = "medium",
                  preferred_provider: Optional[str] = None,
                  max_cost: Optional[float] = None,
                  **kwargs) -> str:
        """Call LLM provider with smart routing, model selection and cost tracking

        Args:
            prompt: User prompt
            system_prompt: System prompt for model behavior
            task_type: Type of task (for routing)
            complexity: Complexity level (for routing)
            preferred_provider: Explicit provider override
            max_cost: Maximum cost per 1K tokens (optional)
            **kwargs: Additional provider-specific options

        Returns:
            Generated text response

        Raises:
            RuntimeError: If all providers fail
        """
        # Select provider
        provider_name = self.select_provider(task_type, complexity, preferred_provider)

        # Select optimal model (NEW)
        optimal_model = self.select_model(provider_name, task_type, complexity, max_cost)

        # Override model in kwargs
        kwargs['model'] = optimal_model

        # Publish LLM_REQUEST event
        request_id = str(uuid.uuid4())[:8]
        try:
            if self.event_bus:
                try:
                    self.event_bus.publish(Event(
                        type=EventType.LLM_REQUEST,
                        data={
                            'model': optimal_model,
                            'provider': provider_name,
                            'tokens_estimated': int(len(prompt) / 4),
                            'request_id': request_id
                        },
                        source='ModelRouter'
                    ))
                except Exception:
                    pass

        except Exception:
            # ignore event publish errors
            pass

        try:
            # Get provider instance (with automatic fallback)
            provider = self.provider_factory.get_provider(provider_name)
            # Generate response
            start_ts = time.time()
            response = provider.generate(prompt, system_prompt, **kwargs)
            duration = time.time() - start_ts

            # Track cost
            self._track_cost(response)

            # Publish LLM_RESPONSE event
            if self.event_bus:
                try:
                    self.event_bus.publish(Event(
                        type=EventType.LLM_RESPONSE,
                        data={
                            'model': getattr(response, 'model', optimal_model),
                            'provider': getattr(response, 'provider', provider_name),
                            'tokens_used': getattr(response, 'tokens_used', None),
                            'duration': duration,
                            'cost': getattr(response, 'cost', None),
                            'request_id': request_id
                        },
                        source='ModelRouter'
                    ))
                except Exception:
                    pass

            # Emit generic inference event for monitoring
            self._emit_inference_event(response)

            # Update provider health
            self._update_provider_health(provider_name, success=True)

            return getattr(response, 'content', response)

        except Exception as e:
            # Update provider health
            self._update_provider_health(provider_name, success=False, error=str(e))

            # Publish LLM_ERROR event
            if self.event_bus:
                try:
                    self.event_bus.publish(Event(
                        type=EventType.LLM_ERROR,
                        data={
                            'model': optimal_model,
                            'provider': provider_name,
                            'error': str(e),
                            'request_id': request_id
                        },
                        source='ModelRouter'
                    ))
                except Exception:
                    pass

            # Log error
            print(f"Error during inference with {provider_name}: {e}")

            # Re-raise
            raise

    def generate(self, prompt: str, **kwargs) -> str:
        """Legacy method for backward compatibility

        Calls call_model with default parameters
        """
        return self.call_model(prompt, **kwargs)

