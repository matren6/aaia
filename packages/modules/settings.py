"""
Configuration Management for AAIA System.

Centralizes all configuration settings with environment-specific overrides.
"""

from dataclasses import dataclass, field
from pathlib import Path
import os


@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    path: str = "data/scribe.db"
    timeout: int = 30
    backup_enabled: bool = True
    backup_interval: int = 3600
    
    def __post_init__(self):
        """Validate configuration values."""
        if self.timeout <= 0:
            raise ValueError("Database timeout must be positive")
        if self.backup_interval <= 0:
            raise ValueError("Backup interval must be positive")


@dataclass
class SchedulerConfig:
    """Scheduler configuration settings."""
    diagnosis_interval: int = 3600
    health_check_interval: int = 1800
    reflection_interval: int = 86400
    evolution_check_interval: int = 7200
    enabled: bool = True
    
    def __post_init__(self):
        """Validate configuration values."""
        if self.diagnosis_interval <= 0:
            raise ValueError("Diagnosis interval must be positive")
        if self.health_check_interval <= 0:
            raise ValueError("Health check interval must be positive")
        if self.reflection_interval <= 0:
            raise ValueError("Reflection interval must be positive")
        if self.evolution_check_interval <= 0:
            raise ValueError("Evolution check interval must be positive")


@dataclass
class LLMConfig:
    """LLM provider configuration."""
    provider: str = "ollama"
    model: str = "phi3"
    base_url: str = "http://localhost:11434"
    timeout: int = 120
    max_retries: int = 3
    max_tokens: int = 4096
    
    def __post_init__(self):
        """Validate configuration values."""
        if self.timeout <= 0:
            raise ValueError("LLM timeout must be positive")
        if self.max_retries < 0:
            raise ValueError("Max retries must be non-negative")
        if self.max_tokens <= 0:
            raise ValueError("Max tokens must be positive")


@dataclass
class EconomicsConfig:
    """Economic system configuration."""
    initial_balance: float = 100.0
    low_balance_threshold: float = 10.0
    inference_cost: float = 0.01
    tool_creation_cost: float = 1.0
    income_generation_enabled: bool = True
    
    def __post_init__(self):
        """Validate configuration values."""
        if self.initial_balance < 0:
            raise ValueError("Initial balance must be non-negative")
        if self.low_balance_threshold < 0:
            raise ValueError("Low balance threshold must be non-negative")
        if self.inference_cost < 0:
            raise ValueError("Inference cost must be non-negative")
        if self.tool_creation_cost < 0:
            raise ValueError("Tool creation cost must be non-negative")


@dataclass
class EvolutionConfig:
    """Evolution system configuration."""
    max_retries: int = 3
    safety_mode: bool = True
    backup_before_modify: bool = True
    max_code_lines: int = 500
    require_tests: bool = False
    
    def __post_init__(self):
        """Validate configuration values."""
        if self.max_retries < 0:
            raise ValueError("Max retries must be non-negative")
        if self.max_code_lines <= 0:
            raise ValueError("Max code lines must be positive")


@dataclass
class ToolsConfig:
    """Tools directory configuration."""
    tools_dir: str = "tools"
    backup_dir: str = "backups"
    auto_discover: bool = True


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_enabled: bool = True
    console_enabled: bool = True


@dataclass
class SystemConfig:
    """Main system configuration combining all sub-configs."""
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    scheduler: SchedulerConfig = field(default_factory=SchedulerConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    economics: EconomicsConfig = field(default_factory=EconomicsConfig)
    evolution: EvolutionConfig = field(default_factory=EvolutionConfig)
    tools: ToolsConfig = field(default_factory=ToolsConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    
    @classmethod
    def from_env(cls):
        """Create configuration from environment variables."""
        return cls(
            database=DatabaseConfig(
                path=os.getenv("DB_PATH", "data/scribe.db"),
                timeout=int(os.getenv("DB_TIMEOUT", "30")),
                backup_enabled=os.getenv("DB_BACKUP_ENABLED", "true").lower() == "true",
                backup_interval=int(os.getenv("DB_BACKUP_INTERVAL", "3600"))
            ),
            scheduler=SchedulerConfig(
                diagnosis_interval=int(os.getenv("DIAGNOSIS_INTERVAL", "3600")),
                health_check_interval=int(os.getenv("HEALTH_CHECK_INTERVAL", "1800")),
                reflection_interval=int(os.getenv("REFLECTION_INTERVAL", "86400")),
                evolution_check_interval=int(os.getenv("EVOLUTION_CHECK_INTERVAL", "7200")),
                enabled=os.getenv("SCHEDULER_ENABLED", "true").lower() == "true"
            ),
            llm=LLMConfig(
                provider=os.getenv("LLM_PROVIDER", "ollama"),
                model=os.getenv("LLM_MODEL", "llama3.2"),
                base_url=os.getenv("LLM_BASE_URL", "http://localhost:11434"),
                timeout=int(os.getenv("LLM_TIMEOUT", "120")),
                max_retries=int(os.getenv("LLM_MAX_RETRIES", "3"))
            ),
            economics=EconomicsConfig(
                initial_balance=float(os.getenv("INITIAL_BALANCE", "100.0")),
                low_balance_threshold=float(os.getenv("LOW_BALANCE_THRESHOLD", "10.0")),
                inference_cost=float(os.getenv("INFERENCE_COST", "0.01")),
                tool_creation_cost=float(os.getenv("TOOL_CREATION_COST", "1.0")),
                income_generation_enabled=os.getenv("INCOME_GENERATION_ENABLED", "true").lower() == "true"
            ),
            evolution=EvolutionConfig(
                max_retries=int(os.getenv("EVOLUTION_MAX_RETRIES", "3")),
                safety_mode=os.getenv("EVOLUTION_SAFETY_MODE", "true").lower() == "true",
                backup_before_modify=os.getenv("EVOLUTION_BACKUP_BEFORE_MODIFY", "true").lower() == "true",
                max_code_lines=int(os.getenv("EVOLUTION_MAX_CODE_LINES", "500")),
                require_tests=os.getenv("EVOLUTION_REQUIRE_TESTS", "false").lower() == "true"
            ),
            tools=ToolsConfig(
                tools_dir=os.getenv("TOOLS_DIR", "tools"),
                backup_dir=os.getenv("BACKUP_DIR", "backups"),
                auto_discover=os.getenv("TOOLS_AUTO_DISCOVER", "true").lower() == "true"
            ),
            logging=LoggingConfig(
                level=os.getenv("LOG_LEVEL", "INFO"),
                format=os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
                file_enabled=os.getenv("LOG_FILE_ENABLED", "true").lower() == "true",
                console_enabled=os.getenv("LOG_CONSOLE_ENABLED", "true").lower() == "true"
            )
        )
    
    @classmethod
    def default(cls):
        """Create default configuration."""
        return cls()
    
    def ensure_directories(self):
        """Ensure all required directories exist."""
        dirs_to_create = [
            Path(self.database.path).parent,
            Path(self.tools.tools_dir),
            Path(self.tools.backup_dir),
        ]
        for directory in dirs_to_create:
            directory.mkdir(parents=True, exist_ok=True)


# Global default configuration instance
_default_config = None


def get_config() -> SystemConfig:
    """Get the global configuration instance (singleton pattern)."""
    global _default_config
    if _default_config is None:
        _default_config = SystemConfig.from_env()
        _default_config.ensure_directories()
    return _default_config


def set_config(config: SystemConfig):
    """Set the global configuration instance (for testing)."""
    global _default_config
    _default_config = config
    _default_config.ensure_directories()


def reset_config():
    """Reset the global configuration to defaults."""
    global _default_config
    _default_config = None


def validate_system_config(config: SystemConfig) -> bool:
    """
    Validate all configuration values before system start.
    
    This function performs comprehensive validation of the entire
    system configuration, ensuring all values are within acceptable
    ranges before the system starts.
    
    Args:
        config: SystemConfig instance to validate
        
    Returns:
        True if validation passes, False otherwise
    """
    errors = []
    
    try:
        # Validate database config
        config.database.__post_init__()
    except ValueError as e:
        errors.append(f"Database config: {e}")
    
    try:
        # Validate scheduler config
        config.scheduler.__post_init__()
    except ValueError as e:
        errors.append(f"Scheduler config: {e}")
    
    try:
        # Validate LLM config
        config.llm.__post_init__()
    except ValueError as e:
        errors.append(f"LLM config: {e}")
    
    try:
        # Validate economics config
        config.economics.__post_init__()
    except ValueError as e:
        errors.append(f"Economics config: {e}")
    
    try:
        # Validate evolution config
        config.evolution.__post_init__()
    except ValueError as e:
        errors.append(f"Evolution config: {e}")
    
    # Validate tools config (directory paths should exist or be creatable)
    tools_path = Path(config.tools.tools_dir)
    if not tools_path.exists():
        try:
            tools_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors.append(f"Tools directory: Cannot create - {e}")
    
    backup_path = Path(config.tools.backup_dir)
    if not backup_path.exists():
        try:
            backup_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors.append(f"Backup directory: Cannot create - {e}")
    
    if errors:
        print("Configuration validation errors:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    return True