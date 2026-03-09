"""
Base Provider Interface for AAIA LLM Integration

Defines the abstract base class and standard response format for all LLM providers.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ModelInfo:
    """Standardized model information across all providers"""
    id: str
    name: str
    provider: str
    capabilities: Dict[str, bool]
    context_window: int
    input_cost_per_1k: float
    output_cost_per_1k: float
    currency: str
    description: Optional[str] = None
    parameter_count: Optional[str] = None

    @property
    def total_cost_per_1k(self) -> float:
        """Combined input + output cost per 1K tokens"""
        return self.input_cost_per_1k + self.output_cost_per_1k

    def meets_requirements(self, 
                          task_type: Optional[str] = None,
                          min_context: Optional[int] = None,
                          max_cost: Optional[float] = None) -> bool:
        """Check if model meets specified requirements"""
        if task_type == 'code' and not self.capabilities.get('code', False):
            return False
        if task_type == 'reasoning' and not self.capabilities.get('reasoning', False):
            return False
        if task_type == 'vision' and not self.capabilities.get('vision', False):
            return False
        if min_context and self.context_window < min_context:
            return False
        if max_cost and self.total_cost_per_1k > max_cost:
            return False
        return True


@dataclass
class LLMResponse:
    """Standard response format from any LLM provider"""
    content: str
    model: str
    tokens_used: int
    cost: float
    provider: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate response data"""
        if not self.content:
            raise ValueError("Response content cannot be empty")
        if self.tokens_used < 0:
            raise ValueError("Token count cannot be negative")
        if self.cost < 0:
            raise ValueError("Cost cannot be negative")


class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers

    All LLM providers (OpenAI, Ollama, Venice, GitHub, Azure) must implement this interface.
    This ensures consistent behavior and cost tracking across different providers.
    """

    @abstractmethod
    def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> LLMResponse:
        """Generate completion from the LLM

        Args:
            prompt: User prompt/question
            system_prompt: System prompt for model behavior
            **kwargs: Provider-specific options (temperature, max_tokens, model, etc.)

        Returns:
            LLMResponse with generated content and metadata

        Raises:
            RuntimeError: If provider is unavailable or request fails
            ValueError: If prompt/parameters are invalid
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is configured and accessible

        Returns:
            True if provider can be used, False if misconfigured or unreachable
        """
        pass

    @abstractmethod
    def get_cost_per_token(self, model: str) -> float:
        """Get cost per token for the model

        Args:
            model: Model name/ID

        Returns:
            Cost in provider's currency (USD, DIEM, etc.) per token
        """
        pass

    @abstractmethod
    def get_available_models(self) -> List[ModelInfo]:
        """Get list of available models with capabilities and pricing

        Returns:
            List of ModelInfo objects describing available models
        """
        pass

    def select_optimal_model(self, 
                           task_type: Optional[str] = None,
                           complexity: str = "medium",
                           max_cost: Optional[float] = None) -> str:
        """Select optimal model based on requirements

        Args:
            task_type: Type of task (code, reasoning, vision, general)
            complexity: low, medium, high
            max_cost: Maximum acceptable cost per 1K tokens

        Returns:
            Model ID string
        """
        models = self.get_available_models()

        context_requirements = {'low': 4096, 'medium': 8192, 'high': 32768}
        min_context = context_requirements.get(complexity, 8192)

        suitable_models = [
            m for m in models 
            if m.meets_requirements(task_type, min_context, max_cost)
        ]

        if not suitable_models:
            return self.config.default_model

        suitable_models.sort(key=lambda m: m.total_cost_per_1k)
        return suitable_models[0].id

    def validate_model(self, model: str) -> bool:
        """Validate if model is supported (optional override)

        Args:
            model: Model name to validate

        Returns:
            True if model is valid, False otherwise
        """
        return True

    def get_model_info(self, model: str) -> Optional[Dict]:
        """Get model metadata (optional override)

        Args:
            model: Model name

        Returns:
            Dict with model info (pricing, capabilities, etc.) or None
        """
        return None


__all__ = ['BaseLLMProvider', 'LLMResponse']
