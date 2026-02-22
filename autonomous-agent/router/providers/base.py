# /opt/autonomous-agent/router/providers/base.py
from abc import ABC, abstractmethod
import logging

class BaseProvider(ABC):
    """Abstract base class for all AI model providers."""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"provider.{name}")
        self.total_cost = 0.0
        self.total_requests = 0
        
    @abstractmethod
    def query(self, prompt: str, max_tokens: int = 4000, temperature: float = 0.7) -> str:
        """Execute a query with the provider."""
        pass
    
    @abstractmethod
    def can_handle(self, prompt: str) -> bool:
        """Check if this provider can handle the given prompt (size, context, etc.)."""
        pass
    
    @abstractmethod
    def estimate_cost(self, prompt: str, max_tokens: int = 4000) -> float:
        """Estimate the cost of a query."""
        pass
    
    @abstractmethod
    def get_available_tokens(self) -> int:
        """Get available tokens/minute or tokens/day for budgeting."""
        pass
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text (can be overridden by providers)."""
        # Default implementation - can be overridden
        return len(text.split()) * 1.3  # Rough approximation
    
    def record_request(self, cost: float):
        """Record a request for tracking."""
        self.total_cost += cost
        self.total_requests += 1
        self.logger.debug(f"Request recorded. Cost: ${cost:.6f}, Total: ${self.total_cost:.6f}")