"""
Dependency Injection Container for AAIA.

Provides centralized dependency management with automatic resolution,
singleton support, and lazy instantiation.
"""

from typing import Dict, Any, Callable, Optional, Type, TypeVar, get_type_hints
import inspect
import threading


T = TypeVar('T')


class DependencyError(Exception):
    """Exception raised for dependency resolution errors."""
    pass


class ServiceDescriptor:
    """Descriptor for a registered service."""
    
    def __init__(self, 
                 implementation: Any, 
                 singleton: bool = False,
                 factory: Optional[Callable] = None):
        self.implementation = implementation
        self.singleton = singleton
        self.factory = factory
        self._instance: Optional[Any] = None
        self._lock = threading.RLock()
        
    def get_instance(self, container: 'Container') -> Any:
        """Get or create an instance of the service."""
        if self.singleton:
            with self._lock:
                if self._instance is None:
                    self._instance = self._create_instance(container)
                return self._instance
        return self._create_instance(container)
    
    def _create_instance(self, container: 'Container') -> Any:
        """Create a new instance of the service."""
        if self.factory is not None:
            return self.factory(container)
        if callable(self.implementation):
            return self.implementation()
        return self.implementation


class Container:
    """
    Dependency Injection Container.
    
    Manages service registration and automatic dependency resolution.
    Supports singleton and transient services, as well as factory functions.
    
    Usage:
        container = Container()
        
        # Register a singleton service
        container.register('Scribe', Scribe, singleton=True)
        
        # Register a service with factory function (for dependencies)
        container.register('EconomicManager', lambda c: EconomicManager(c.get('Scribe')))
        
        # Get an instance
        scribe = container.get('Scribe')
    """
    
    def __init__(self):
        self._services: Dict[str, ServiceDescriptor] = {}
        self._aliases: Dict[str, str] = {}  # Interface name -> service name
        self._lock = threading.RLock()
        
    def register(self, 
                 name: str, 
                 implementation: Any, 
                 singleton: bool = False,
                 alias: Optional[str] = None) -> 'Container':
        """
        Register a service with the container.
        
        Args:
            name: Unique identifier for the service
            implementation: Class, instance, or factory function
            singleton: If True, return the same instance every time
            alias: Optional alias for the service (for interface-based lookups)
            
        Returns:
            Self, for method chaining
        """
        with self._lock:
            # Determine if implementation is a factory (takes container as arg)
            factory = None
            if callable(implementation):
                sig = inspect.signature(implementation)
                params = list(sig.parameters.keys())
                # Check if first parameter hints at container injection
                if params and len(params) <= 1:
                    # Assume it's a factory if it takes no args or has container hint
                    if len(params) == 0:
                        factory = lambda c: implementation()
                    else:
                        factory = implementation
            
            self._services[name] = ServiceDescriptor(
                implementation=implementation,
                singleton=singleton,
                factory=factory
            )
            
            # Register alias if provided
            if alias is not None:
                self._aliases[alias] = name
                
        return self
    
    def register_instance(self, name: str, instance: Any, alias: Optional[str] = None) -> 'Container':
        """
        Register an existing instance as a singleton.
        
        Args:
            name: Unique identifier for the service
            instance: Pre-created instance to register
            alias: Optional alias for the service
            
        Returns:
            Self, for method chaining
        """
        with self._lock:
            self._services[name] = ServiceDescriptor(
                implementation=lambda: instance,
                singleton=True
            )
            if alias is not None:
                self._aliases[alias] = name
        return self
    
    def register_factory(self, name: str, factory: Callable[['Container'], Any], 
                        singleton: bool = False) -> 'Container':
        """
        Register a factory function that receives the container.
        
        Args:
            name: Unique identifier for the service
            factory: Function that takes container and returns instance
            singleton: If True, cache the result
            
        Returns:
            Self, for method chaining
        """
        with self._lock:
            self._services[name] = ServiceDescriptor(
                implementation=lambda: None,  # Not used when factory provided
                singleton=singleton,
                factory=factory
            )
        return self
    
    def get(self, name: str) -> Any:
        """
        Get a service by name.
        
        Args:
            name: The service name or alias to resolve
            
        Returns:
            The service instance
            
        Raises:
            DependencyError: If service is not registered
        """
        with self._lock:
            # Resolve alias
            resolved_name = self._aliases.get(name, name)
            
            if resolved_name not in self._services:
                raise DependencyError(f"Service '{name}' is not registered")
                
            descriptor = self._services[resolved_name]
            
        return descriptor.get_instance(self)
    
    def get_optional(self, name: str, default: Any = None) -> Any:
        """
        Get a service by name, returning default if not found.
        
        Args:
            name: The service name to resolve
            default: Value to return if service is not registered
            
        Returns:
            The service instance or default
        """
        try:
            return self.get(name)
        except DependencyError:
            return default
    
    def has(self, name: str) -> bool:
        """
        Check if a service is registered.
        
        Args:
            name: The service name to check
            
        Returns:
            True if service is registered
        """
        with self._lock:
            return name in self._services or name in self._aliases
            
    def unregister(self, name: str) -> bool:
        """
        Unregister a service.
        
        Args:
            name: The service name to remove
            
        Returns:
            True if service was removed, False if not found
        """
        with self._lock:
            if name in self._services:
                del self._services[name]
                # Remove any aliases pointing to this service
                self._aliases = {k: v for k, v in self._aliases.items() if v != name}
                return True
            return False
    
    def clear(self) -> None:
        """Clear all registered services."""
        with self._lock:
            self._services.clear()
            self._aliases.clear()
    
    def create_scope(self) -> 'Container':
        """
        Create a child container that inherits all services.
        
        Child containers can override parent services while
        maintaining the parent's services as defaults.
        
        Returns:
            A new child container
        """
        child = Container()
        with self._lock:
            child._services = dict(self._services)
            child._aliases = dict(self._aliases)
        return child
    
    def resolve_dependencies(self, cls: Type[T], **overrides: Any) -> T:
        """
        Automatically resolve dependencies for a class constructor.
        
        Args:
            cls: The class to instantiate
            **overrides: Explicit values for specific parameters
            
        Returns:
            Instance of the class with resolved dependencies
            
        Raises:
            DependencyError: If a required dependency cannot be resolved
        """
        try:
            hints = get_type_hints(cls.__init__)
        except Exception:
            hints = {}
            
        sig = inspect.signature(cls.__init__)
        kwargs = {}
        
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
                
            if param_name in overrides:
                kwargs[param_name] = overrides[param_name]
            elif param_name in hints:
                type_name = hints[param_name].__name__
                try:
                    kwargs[param_name] = self.get(type_name)
                except DependencyError:
                    if param.default is inspect.Parameter.empty:
                        raise DependencyError(
                            f"Cannot resolve dependency '{param_name}' for {cls.__name__}"
                        )
            elif param.default is inspect.Parameter.empty:
                raise DependencyError(
                    f"Cannot resolve dependency '{param_name}' for {cls.__name__}"
                )
                
        return cls(**kwargs)
    
    def get_registered_services(self) -> list[str]:
        """Get list of all registered service names."""
        with self._lock:
            return list(self._services.keys())


# Global container instance
_container: Optional[Container] = None


def get_container() -> Container:
    """Get the global container instance (singleton pattern)."""
    global _container
    if _container is None:
        _container = Container()
    return _container


def set_container(container: Container) -> None:
    """Set the global container instance (for testing)."""
    global _container
    _container = container


def reset_container() -> None:
    """Reset the global container."""
    global _container
    _container = None


# Decorator for automatic dependency injection
def injectable(cls: Type[T]) -> Type[T]:
    """
    Class decorator that enables automatic dependency injection.
    
    The class constructor will receive dependencies from the global container.
    
    Usage:
        @injectable
        class MyService:
            def __init__(self, scribe: 'Scribe', config: 'SystemConfig'):
                self.scribe = scribe
                self.config = config
    """
    original_init = cls.__init__
    
    def new_init(self, *args, **kwargs):
        container = get_container()
        
        # Get type hints for __init__
        try:
            hints = get_type_hints(original_init)
        except Exception:
            hints = {}
            
        # Resolve missing arguments from container
        sig = inspect.signature(original_init)
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            if param_name not in kwargs and param_name in hints:
                type_hint = hints[param_name]
                if hasattr(type_hint, '__name__'):
                    try:
                        kwargs[param_name] = container.get(type_hint.__name__)
                    except DependencyError:
                        if param.default is inspect.Parameter.empty:
                            pass  # Let it fail naturally
        
        original_init(self, *args, **kwargs)
        
    cls.__init__ = new_init
    return cls
