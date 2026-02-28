"""
Setup Module for AAIA - Integrates Config, Event Bus, and Container.

This module provides helper functions to set up the system with:
- Centralized configuration management
- Event-driven communication
- Dependency injection container

All integrations are optional and backward-compatible with existing code.
"""

from typing import Optional, Callable, Any
import threading

# Import the new architectural components
from modules.settings import (
    SystemConfig, 
    get_config, 
    set_config, 
    DatabaseConfig,
    SchedulerConfig,
    LLMConfig,
    EconomicsConfig,
    EvolutionConfig,
    ToolsConfig,
    LoggingConfig
)

from modules.bus import (
    EventBus, 
    EventType, 
    Event,
    get_event_bus,
    set_event_bus
)

from modules.container import (
    Container,
    get_container,
    set_container,
    DependencyError
)

# Import existing modules for registration
from modules.scribe import Scribe
from modules.economics import EconomicManager
from modules.mandates import MandateEnforcer
from modules.router import ModelRouter
from modules.dialogue import DialogueManager
from modules.forge import Forge
from modules.scheduler import AutonomousScheduler
from modules.goals import GoalSystem
from modules.hierarchy_manager import HierarchyManager
from modules.self_diagnosis import SelfDiagnosis
from modules.self_modification import SelfModification
from modules.evolution import EvolutionManager
from modules.metacognition import MetaCognition
from modules.capability_discovery import CapabilityDiscovery
from modules.intent_predictor import IntentPredictor
from modules.environment_explorer import EnvironmentExplorer
from modules.strategy_optimizer import StrategyOptimizer
from modules.evolution_orchestrator import EvolutionOrchestrator
from modules.evolution_pipeline import EvolutionPipeline


class SystemBuilder:
    """
    Builder class for setting up the AAIA system with all new components.
    
    Provides a fluent API for configuring and building the system with
    config, event bus, and dependency injection container.
    """
    
    def __init__(self, config: Optional[SystemConfig] = None):
        self._config = config or get_config()
        self._event_bus = EventBus(enable_logging=False)  # Create instance
        self._container = Container()
        self._modules = {}
        self._initialized = False
        self._lock = threading.RLock()
        
    def with_config(self, config: SystemConfig) -> 'SystemBuilder':
        """Set a custom configuration."""
        self._config = config
        return self
        
    def with_logging(self, enabled: bool = True) -> 'SystemBuilder':
        """Enable event bus logging."""
        self._event_bus = EventBus(enable_logging=enabled)
        return self
        
    def build(self) -> dict:
        """
        Build and initialize all system components.
        
        Returns:
            Dictionary containing all initialized modules and systems
        """
        with self._lock:
            if self._initialized:
                raise RuntimeError("System already built")
                
            # Ensure config directories exist
            self._config.ensure_directories()
            
            # Register EventBus first as it's needed by many modules
            self._container.register_instance('EventBus', self._event_bus)
            
            # Register core services in container
            self._register_core_services()
            
            # Register autonomous services
            self._register_autonomous_services()
            
            # Register self-development services
            self._register_development_services()
            
            # Initialize all modules from container
            self._initialize_modules()
            
            # Set up event subscriptions
            self._setup_event_subscriptions()
            
            self._initialized = True
            
            return {
                'config': self._config,
                'event_bus': self._event_bus,
                'container': self._container,
                'modules': self._modules
            }
    
    def _register_core_services(self):
        """Register core services in the container."""
        config = self._config
        
        # Scribe (core logging) - singleton
        self._container.register_factory('Scribe', 
            lambda c: Scribe(config.database.path), 
            singleton=True)
            
        # Economic Manager
        self._container.register_factory('EconomicManager',
            lambda c: EconomicManager(c.get('Scribe'), c.get('EventBus')),
            singleton=True)
            
        # Mandate Enforcer
        self._container.register_factory('MandateEnforcer',
            lambda c: MandateEnforcer(c.get('Scribe')),
            singleton=True)
            
        # Model Router
        self._container.register_factory('ModelRouter',
            lambda c: ModelRouter(c.get('EconomicManager'), c.get('EventBus')),
            singleton=True)
            
        # Dialogue Manager
        self._container.register_factory('DialogueManager',
            lambda c: DialogueManager(c.get('Scribe'), c.get('ModelRouter')),
            singleton=True)
            
        # Forge (tool creation)
        self._container.register_factory('Forge',
            lambda c: Forge(c.get('ModelRouter'), c.get('Scribe'), event_bus=c.get('EventBus')),
            singleton=True)
    
    def _register_autonomous_services(self):
        """Register autonomous module services."""
        # Scheduler
        self._container.register_factory('AutonomousScheduler',
            lambda c: AutonomousScheduler(
                c.get('Scribe'),
                c.get('ModelRouter'),
                c.get('EconomicManager'),
                c.get('Forge'),
                container=c,  # Pass container to avoid circular deps
                event_bus=c.get('EventBus')
            ),
            singleton=True)
            
        # Goal System
        self._container.register_factory('GoalSystem',
            lambda c: GoalSystem(
                c.get('Scribe'),
                c.get('ModelRouter'),
                c.get('EconomicManager')
            ),
            singleton=True)
            
        # Hierarchy Manager
        self._container.register_factory('HierarchyManager',
            lambda c: HierarchyManager(
                c.get('Scribe'),
                c.get('EconomicManager')
            ),
            singleton=True)
            
    def _register_development_services(self):
        """Register self-development module services."""
        # Self Diagnosis
        self._container.register_factory('SelfDiagnosis',
            lambda c: SelfDiagnosis(
                c.get('Scribe'),
                c.get('ModelRouter'),
                c.get('Forge'),
                goals=c.get('GoalSystem'),  # Pass goals to avoid undefined attribute
                event_bus=c.get('EventBus')
            ),
            singleton=True)
            
        # Self Modification
        self._container.register_factory('SelfModification',
            lambda c: SelfModification(
                c.get('Scribe'),
                c.get('ModelRouter'),
                c.get('Forge'),
                event_bus=c.get('EventBus')
            ),
            singleton=True)
            
        # Evolution Manager
        self._container.register_factory('EvolutionManager',
            lambda c: EvolutionManager(
                c.get('Scribe'),
                c.get('ModelRouter'),
                c.get('Forge'),
                c.get('SelfDiagnosis'),
                c.get('SelfModification'),
                c.get('EventBus')
            ),
            singleton=True)
            
        # Evolution Pipeline
        self._container.register_factory('EvolutionPipeline',
            lambda c: EvolutionPipeline(
                c.get('Scribe'),
                c.get('ModelRouter'),
                c.get('Forge'),
                c.get('SelfDiagnosis'),
                c.get('SelfModification'),
                c.get('EvolutionManager')
            ),
            singleton=True)
            
        # MetaCognition
        self._container.register_factory('MetaCognition',
            lambda c: MetaCognition(
                c.get('Scribe'),
                c.get('ModelRouter'),
                c.get('SelfDiagnosis'),
                event_bus=c.get('EventBus')
            ),
            singleton=True)
            
        # Capability Discovery
        self._container.register_factory('CapabilityDiscovery',
            lambda c: CapabilityDiscovery(
                c.get('Scribe'),
                c.get('ModelRouter'),
                c.get('Forge'),
                event_bus=c.get('EventBus')
            ),
            singleton=True)
            
        # Intent Predictor
        self._container.register_factory('IntentPredictor',
            lambda c: IntentPredictor(
                c.get('Scribe'),
                c.get('ModelRouter'),
                event_bus=c.get('EventBus')
            ),
            singleton=True)
            
        # Environment Explorer
        self._container.register_factory('EnvironmentExplorer',
            lambda c: EnvironmentExplorer(
                c.get('Scribe'),
                c.get('ModelRouter'),
                event_bus=c.get('EventBus')
            ),
            singleton=True)
            
        # Strategy Optimizer
        self._container.register_factory('StrategyOptimizer',
            lambda c: StrategyOptimizer(
                c.get('Scribe'),
                event_bus=c.get('EventBus')
            ),
            singleton=True)
            
        # Evolution Orchestrator
        self._container.register_factory('EvolutionOrchestrator',
            lambda c: EvolutionOrchestrator(
                c.get('Scribe'),
                c.get('ModelRouter'),
                c.get('Forge'),
                c.get('SelfDiagnosis'),
                c.get('SelfModification'),
                c.get('MetaCognition'),
                c.get('CapabilityDiscovery'),
                c.get('IntentPredictor'),
                c.get('EnvironmentExplorer'),
                c.get('StrategyOptimizer'),
                event_bus=c.get('EventBus')
            ),
            singleton=True)
            
    def _initialize_modules(self):
        """Initialize all modules from container."""
        service_names = [
            'Scribe', 'EconomicManager', 'MandateEnforcer', 'ModelRouter',
            'DialogueManager', 'Forge', 'AutonomousScheduler', 'GoalSystem',
            'HierarchyManager', 'SelfDiagnosis', 'SelfModification',
            'EvolutionManager', 'EvolutionPipeline', 'MetaCognition',
            'CapabilityDiscovery', 'IntentPredictor', 'EnvironmentExplorer',
            'StrategyOptimizer', 'EvolutionOrchestrator'
        ]
        
        for name in service_names:
            try:
                self._modules[name] = self._container.get(name)
            except DependencyError as e:
                print(f"Warning: Failed to initialize {name}: {e}")
                
    def _setup_event_subscriptions(self):
        """Set up event subscriptions for decoupled communication."""
        # Subscribe to economic events for low balance warnings
        self._event_bus.subscribe(
            EventType.ECONOMIC_TRANSACTION,
            self._handle_economic_transaction
        )
        
        # Subscribe to evolution events
        self._event_bus.subscribe(
            EventType.EVOLUTION_COMPLETED,
            self._handle_evolution_completed
        )
        
        # Subscribe to system health events
        self._event_bus.subscribe(
            EventType.SYSTEM_HEALTH_CHECK,
            self._handle_health_check
        )
        
    def _handle_economic_transaction(self, event: Event):
        """Handle economic transaction events."""
        balance = event.data.get('balance_after', 0)
        threshold = self._config.economics.low_balance_threshold
        
        if balance < threshold:
            # Publish low balance event
            self._event_bus.publish(Event(
                type=EventType.BALANCE_LOW,
                data={
                    'balance': balance,
                    'threshold': threshold
                },
                source='SystemBuilder'
            ))
            
    def _handle_evolution_completed(self, event: Event):
        """Handle evolution completed events."""
        print(f"[EVENT] Evolution completed: {event.data.get('summary', 'N/A')}")
        
    def _handle_health_check(self, event: Event):
        """Handle health check events."""
        print(f"[EVENT] Health check: {event.data.get('status', 'unknown')}")
        
    def get_module(self, name: str):
        """Get a module by name."""
        return self._modules.get(name)
        
    def get_all_modules(self) -> dict:
        """Get all initialized modules."""
        return self._modules.copy()


def create_system(config: Optional[SystemConfig] = None) -> dict:
    """
    Create and initialize the AAIA system with all components.
    
    Args:
        config: Optional custom configuration
        
    Returns:
        Dictionary with 'config', 'event_bus', 'container', and 'modules'
    """
    builder = SystemBuilder(config)
    return builder.build()


def get_system_from_container(container: Container) -> dict:
    """
    Get all modules from an existing container.
    
    Args:
        container: Pre-configured container
        
    Returns:
        Dictionary of module name -> instance
    """
    modules = {}
    service_names = [
        'Scribe', 'EconomicManager', 'MandateEnforcer', 'ModelRouter',
        'DialogueManager', 'Forge', 'AutonomousScheduler', 'GoalSystem',
        'HierarchyManager', 'SelfDiagnosis', 'SelfModification',
        'EvolutionManager', 'EvolutionPipeline', 'MetaCognition',
        'CapabilityDiscovery', 'IntentPredictor', 'EnvironmentExplorer',
        'StrategyOptimizer', 'EvolutionOrchestrator'
    ]
    
    for name in service_names:
        try:
            modules[name] = container.get(name)
        except DependencyError:
            pass
            
    return modules


# Example usage and demonstration
if __name__ == "__main__":
    print("=" * 60)
    print("AAIA System Builder - Demo")
    print("=" * 60)
    
    # Create system with new architecture
    system = create_system()
    
    print("\n✓ System created with:")
    print(f"  - Configuration: {type(system['config']).__name__}")
    print(f"  - Event Bus: {type(system['event_bus']).__name__}")
    print(f"  - Container: {type(system['container']).__name__}")
    print(f"  - Modules: {len(system['modules'])} initialized")
    
    print("\nRegistered services in container:")
    for service in system['container'].get_registered_services():
        print(f"  - {service}")
    
    # Demonstrate event publishing
    print("\n✓ Demonstrating event system:")
    system['event_bus'].publish(Event(
        type=EventType.SYSTEM_STARTUP,
        data={'message': 'System initialized via builder'},
        source='Demo'
    ))
    
    # Get event history
    history = system['event_bus'].get_history()
    print(f"  Event history: {len(history)} events")
    
    print("\n✓ All systems operational!")