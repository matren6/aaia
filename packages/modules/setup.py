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
from modules.database_manager import get_database_manager, DatabaseManager
from modules.economics import EconomicManager
from modules.mandates import MandateEnforcer
from modules.router import ModelRouter
from modules.dialogue import DialogueManager
from modules.forge import Forge
from modules.scheduler import AutonomousScheduler
from modules.goals import GoalSystem
from modules.hierarchy_manager import HierarchyManager
from modules.self_diagnosis import SelfDiagnosis
#from modules.self_modification import SelfModification
from modules.nix_aware_self_modification import NixAwareSelfModification
from modules.evolution import EvolutionManager
from modules.metacognition import MetaCognition
from modules.capability_discovery import CapabilityDiscovery
from modules.intent_predictor import IntentPredictor
from modules.environment_explorer import EnvironmentExplorer
from modules.strategy_optimizer import StrategyOptimizer
from modules.evolution_orchestrator import EvolutionOrchestrator
from modules.evolution_pipeline import EvolutionPipeline
from modules.prompt_manager import get_prompt_manager
from modules.prompt_optimizer import PromptOptimizer

# Import new Phase 2-3 modules
from modules.master_model import MasterModelManager
from modules.income_seeker import IncomeSeeker

# Import new Phase 5 modules (Automation & Intelligence)
from modules.trait_extractor import TraitExtractor, AutonomousTraitLearning
from modules.reflection_analyzer import ReflectionAnalyzer
from modules.profitability_reporter import ProfitabilityReporter

# Import Phase 1 modules (Resource Monitoring)
from modules.resource_monitor import ResourceMonitor

# Import Phase 2 modules (Marginal Analysis)
from modules.marginal_analyzer import MarginalAnalyzer

# Import Phase 3 modules (Crisis Response)
from modules.economic_crisis_handler import EconomicCrisisHandler

# Import LLM tracking module
from modules.llm_tracker import LLMInteractionTracker


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
            
            # Register configuration in container for services that expect it
            self._container.register_instance('SystemConfig', self._config)

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
        
        # Database manager - singleton
        self._container.register_factory('DatabaseManager',
            lambda c: get_database_manager(config.database.path),
            singleton=True)

        # Scribe (core logging) - singleton (uses DatabaseManager)
        self._container.register_factory('Scribe', 
            lambda c: Scribe(db_manager=c.get('DatabaseManager')), 
            singleton=True)

        # PromptManager - singleton
        self._container.register_factory('PromptManager',
            lambda c: get_prompt_manager(),
            singleton=True)
            
        # Economic Manager
        self._container.register_factory('EconomicManager',
            lambda c: EconomicManager(
                c.get('Scribe'),
                event_bus=c.get('EventBus')
            ),
            singleton=True)
            
        # Mandate Enforcer (Enhanced in Phase 3)
        self._container.register_factory('MandateEnforcer',
            lambda c: MandateEnforcer(
                c.get('Scribe'),
                prompt_manager=c.get('PromptManager'),
                router=c.get('ModelRouter'),
                database_manager=c.get('DatabaseManager'),
                event_bus=c.get('EventBus')
            ),
            singleton=True)
            
        # Model Router (Phase 2: with MarginalAnalyzer)
        # Note: MarginalAnalyzer must be registered first
        def create_router(c):
            try:
                marginal_analyzer = c.get('MarginalAnalyzer')
            except:
                marginal_analyzer = None

            return ModelRouter(
                c.get('EconomicManager'),
                event_bus=c.get('EventBus'),
                prompt_manager=c.get('PromptManager'),
                config=c.get('SystemConfig'),
                marginal_analyzer=marginal_analyzer
            )

        self._container.register_factory('ModelRouter',
            create_router,
            singleton=True)
            
        # Dialogue Manager (Enhanced in Phase 3)
        self._container.register_factory('DialogueManager',
            lambda c: DialogueManager(
                c.get('Scribe'),
                c.get('ModelRouter'),
                prompt_manager=c.get('PromptManager'),
                event_bus=c.get('EventBus')
            ),
            singleton=True)
            
        # Forge (tool creation)
        self._container.register_factory('Forge',
            lambda c: Forge(c.get('ModelRouter'), c.get('Scribe'), event_bus=c.get('EventBus'), prompt_manager=c.get('PromptManager')),
            singleton=True)

        # Master Model Manager (Phase 2.1)
        self._container.register_factory('MasterModelManager',
            lambda c: MasterModelManager(
                c.get('Scribe'),
                c.get('DatabaseManager'),
                c.get('PromptManager'),
                c.get('ModelRouter'),
                event_bus=c.get('EventBus')
            ),
            singleton=True)

        # Master Well-Being Monitor (Phase 2.2 - Tier 1 requirement)
        from modules.master_wellbeing import MasterWellBeingMonitor
        self._container.register_factory('MasterWellBeingMonitor',
            lambda c: MasterWellBeingMonitor(
                c.get('Scribe'),
                c.get('DatabaseManager'),
                c.get('MasterModelManager'),
                c.get('PromptManager'),
                c.get('ModelRouter'),
                event_bus=c.get('EventBus')
            ),
            singleton=True)

        # LLM Interaction Tracker (Phase 2.3 - Tracking & Analysis)
        from modules.llm_tracker import LLMInteractionTracker
        self._container.register_factory('LLMInteractionTracker',
            lambda c: LLMInteractionTracker(
                c.get('DatabaseManager'),
                c.get('Scribe'),
                event_bus=c.get('EventBus')
            ),
            singleton=True)

        # ResourceMonitor (Phase 1)
        self._container.register_factory('ResourceMonitor',
            lambda c: ResourceMonitor(
                c.get('EconomicManager'),
                c.get('Scribe'),
                event_bus=c.get('EventBus'),
                config=c.get('SystemConfig')
            ),
            singleton=True)

        # Web Server (UI Dashboard) - optional dependency
        try:
            from modules.web_server import WebServer
            from modules.web_dashboard_data import DashboardDataAggregator

            # Register data aggregator first
            self._container.register_factory('DashboardDataAggregator',
                lambda c: DashboardDataAggregator(
                    scribe=c.get('Scribe'),
                    economics=c.get('EconomicManager'),
                    goals=c.get('GoalSystem'),
                    scheduler=c.get('AutonomousScheduler'),
                    hierarchy=c.get('HierarchyManager'),
                    master_model=c.get('MasterModelManager'),
                    container=c,
                    config=c.get('SystemConfig')
                ),
                singleton=True)

            # Register web server with data aggregator
            self._container.register_factory('WebServer',
                lambda c: WebServer(
                    event_bus=c.get('EventBus'),
                    container=c,
                    config=c.get('SystemConfig'),
                    data_aggregator=c.get('DashboardDataAggregator')
                ),
                singleton=True)
        except ImportError as e:
            print(f"[INFO] Web server dependencies not available: {e}")
            print("[INFO] Web dashboard will be disabled. Install flask, flask-socketio, flask-cors to enable.")
            # Register stub factories that return None
            self._container.register_factory('DashboardDataAggregator', lambda c: None, singleton=True)
            self._container.register_factory('WebServer', lambda c: None, singleton=True)

        # MarginalAnalyzer (Phase 2)
        self._container.register_factory('MarginalAnalyzer',
            lambda c: MarginalAnalyzer(
                self._config.database.path,
                c.get('Scribe'),
                c.get('EconomicManager')
            ),
            singleton=True)

        # EconomicCrisisHandler (Phase 3)
        # Note: Must be registered after HierarchyManager, Scheduler, IncomeSeeker
        def create_crisis_handler(c):
            try:
                return EconomicCrisisHandler(
                    c.get('Scribe'),
                    c.get('HierarchyManager'),
                    c.get('AutonomousScheduler'),
                    c.get('IncomeSeeker'),
                    c.get('EconomicManager'),
                    event_bus=c.get('EventBus')
                )
            except Exception as e:
                # Return a stub if dependencies not available yet
                from modules.scribe import Scribe
                return EconomicCrisisHandler(
                    c.get('Scribe'),
                    None, None, None,
                    c.get('EconomicManager'),
                    event_bus=c.get('EventBus')
                )

        self._container.register_factory('EconomicCrisisHandler',
            create_crisis_handler,
            singleton=True)
    
    def _register_autonomous_services(self):
        """Register autonomous module services."""
        # Income Seeker (Phase 2.2)
        self._container.register_factory('IncomeSeeker',
            lambda c: IncomeSeeker(
                c.get('EconomicManager'),
                c.get('PromptManager'),
                c.get('ModelRouter'),
                c.get('Scribe'),
                c.get('GoalSystem'),
                event_bus=c.get('EventBus')
            ),
            singleton=True)

        # Scheduler
        self._container.register_factory('AutonomousScheduler',
             lambda c: AutonomousScheduler(
                 c.get('Scribe'),
                 c.get('ModelRouter'),
                 c.get('EconomicManager'),
                 c.get('Forge'),
                 container=c,  # Pass container to avoid circular deps
                 event_bus=c.get('EventBus'),
                 prompt_manager=c.get('PromptManager')
             ),
             singleton=True)
            
        # Goal System
        self._container.register_factory('GoalSystem',
            lambda c: GoalSystem(
                c.get('Scribe'),
                c.get('ModelRouter'),
                c.get('EconomicManager'),
                prompt_manager=c.get('PromptManager'),
                event_bus=c.get('EventBus')
            ),
            singleton=True)
            
        # Hierarchy Manager
        self._container.register_factory('HierarchyManager',
            lambda c: HierarchyManager(
                c.get('Scribe'),
                c.get('EconomicManager'),
                event_bus=c.get('EventBus')
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
                event_bus=c.get('EventBus'),
                prompt_manager=c.get('PromptManager')
            ),
            singleton=True)
            
        # Self Modification
        self._container.register_factory('SelfModification',
            lambda c: NixAwareSelfModification(
                c.get('Scribe'),
                c.get('ModelRouter'),
                c.get('Forge'),
                event_bus=c.get('EventBus'),
                prompt_manager=c.get('PromptManager')
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
                event_bus=c.get('EventBus'),
                prompt_manager=c.get('PromptManager')
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
                c.get('EvolutionManager'),
                event_bus=c.get('EventBus'),
                prompt_manager=c.get('PromptManager')
            ),
            singleton=True)
            
        # MetaCognition
        self._container.register_factory('MetaCognition',
            lambda c: MetaCognition(
                c.get('Scribe'),
                c.get('ModelRouter'),
                event_bus=c.get('EventBus'),
                prompt_manager=c.get('PromptManager')
            ),
            singleton=True)
            
        # Capability Discovery
        self._container.register_factory('CapabilityDiscovery',
            lambda c: CapabilityDiscovery(
                c.get('Scribe'),
                c.get('ModelRouter'),
                c.get('Forge'),
                event_bus=c.get('EventBus'),
                prompt_manager=c.get('PromptManager')
            ),
            singleton=True)
            
        # Intent Predictor
        self._container.register_factory('IntentPredictor',
            lambda c: IntentPredictor(
                c.get('Scribe'),
                c.get('ModelRouter'),
                event_bus=c.get('EventBus'),
                prompt_manager=c.get('PromptManager')
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
                router=c.get('ModelRouter'),
                evolution=c.get('EvolutionManager'),
                metacognition=c.get('MetaCognition'),
                event_bus=c.get('EventBus'),
                prompt_manager=c.get('PromptManager')
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
                event_bus=c.get('EventBus'),
                prompt_manager=c.get('PromptManager')
            ),
            singleton=True)

        # Phase 5: Automation & Intelligence modules
        # Trait Extractor
        self._container.register_factory('TraitExtractor',
            lambda c: TraitExtractor(
                c.get('PromptManager'),
                c.get('ModelRouter'),
                c.get('Scribe'),
                event_bus=c.get('EventBus')
            ),
            singleton=True)

        # Autonomous Trait Learning
        self._container.register_factory('AutonomousTraitLearning',
            lambda c: AutonomousTraitLearning(
                c.get('MasterModelManager'),
                c.get('TraitExtractor'),
                c.get('Scribe'),
                event_bus=c.get('EventBus')
            ),
            singleton=True)

        # Reflection Analyzer
        self._container.register_factory('ReflectionAnalyzer',
            lambda c: ReflectionAnalyzer(
                c.get('PromptManager'),
                c.get('ModelRouter'),
                c.get('Scribe'),
                event_bus=c.get('EventBus')
            ),
            singleton=True)

        # Profitability Reporter
        self._container.register_factory('ProfitabilityReporter',
            lambda c: ProfitabilityReporter(
                c.get('EconomicManager'),
                c.get('PromptManager'),
                c.get('ModelRouter'),
                c.get('Scribe'),
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
            'StrategyOptimizer', 'EvolutionOrchestrator', 'PromptManager',
            # Phase 5 modules
            'MasterModelManager', 'IncomeSeeker', 'TraitExtractor',
            'AutonomousTraitLearning', 'ReflectionAnalyzer', 'ProfitabilityReporter'
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
        'StrategyOptimizer', 'EvolutionOrchestrator', 'PromptManager'
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