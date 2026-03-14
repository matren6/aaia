"""
Configuration Management for AAIA System.

Centralizes all configuration settings with environment-specific overrides.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import os

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


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
    # Additional scheduler settings
    max_concurrent_tasks: int = 3
    task_timeout: int = 300
    retry_failed_tasks: bool = True
    max_task_retries: int = 2
    
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
class ProviderConfig:
    """Base provider configuration"""
    enabled: bool = False
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    timeout: int = 120
    max_retries: int = 3


@dataclass
class OllamaConfig(ProviderConfig):
    """Ollama provider configuration"""
    enabled: bool = True
    base_url: str = "http://localhost:11434"
    default_model: str = "phi3"


@dataclass
class OpenAIConfig(ProviderConfig):
    """OpenAI provider configuration"""
    enabled: bool = False
    base_url: str = "https://api.openai.com/v1"
    default_model: str = "gpt-4o-mini"
    organization: Optional[str] = None
    max_tokens: int = 4096


@dataclass
class GitHubModelsConfig(ProviderConfig):
    """GitHub Models API configuration"""
    enabled: bool = False
    default_model: str = "gpt-4o"


@dataclass
class AzureOpenAIConfig(ProviderConfig):
    """Azure OpenAI configuration"""
    enabled: bool = False
    base_url: Optional[str] = None
    deployment_name: Optional[str] = None
    api_version: str = "2024-02-01"


@dataclass
class VeniceAIConfig(ProviderConfig):
    """Venice AI provider configuration"""
    enabled: bool = False
    base_url: str = "https://api.venice.ai/api/v1"
    default_model: str = "llama-3.3-70b"
    check_diem_before_request: bool = True
    diem_warning_threshold: float = 1.0
    diem_critical_threshold: float = 0.1
    auto_fallback_on_low_diem: bool = True


@dataclass
class LLMConfig:
    """Unified LLM configuration for multi-provider system"""
    default_provider: str = "ollama"
    fallback_provider: Optional[str] = None

    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    openai: OpenAIConfig = field(default_factory=OpenAIConfig)
    github: GitHubModelsConfig = field(default_factory=GitHubModelsConfig)
    azure: AzureOpenAIConfig = field(default_factory=AzureOpenAIConfig)
    venice: VeniceAIConfig = field(default_factory=VeniceAIConfig)

    def __post_init__(self):
        """Validate LLM configuration."""
        valid_providers = ['ollama', 'openai', 'github', 'azure', 'venice']
        if self.default_provider not in valid_providers:
            raise ValueError(f"Default provider must be one of {valid_providers}")
        if self.fallback_provider and self.fallback_provider not in valid_providers:
            raise ValueError(f"Fallback provider must be one of {valid_providers}")


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
    # Additional evolution settings
    validation_timeout: int = 30
    rollback_on_error: bool = True
    max_modifications_per_cycle: int = 5
    modification_cooldown: int = 300
    
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
    # Extra tool-related configuration
    max_tool_size_kb: int = 500
    allow_network_tools: bool = False
    sandbox_mode: bool = True
    execution_timeout: int = 30


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_enabled: bool = True
    console_enabled: bool = True


@dataclass
class NetworkConfig:
    """Network configuration."""
    enabled: bool = True
    timeout: int = 30
    max_retries: int = 3
    retry_delay: int = 1
    verify_ssl: bool = True
    proxy_url: Optional[str] = None
    user_agent: str = "AAIA/1.0"


@dataclass
class MonitoringConfig:
    """Monitoring and observability configuration."""
    enabled: bool = True
    log_level: str = "INFO"
    log_to_file: bool = True
    log_file_path: str = "logs/aaia.log"
    log_rotation_mb: int = 10
    log_retention_days: int = 7
    metrics_enabled: bool = True
    metrics_interval: int = 60


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
    network: NetworkConfig = field(default_factory=NetworkConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    
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
                default_provider=os.getenv("LLM_DEFAULT_PROVIDER", "ollama"),
                fallback_provider=os.getenv("LLM_FALLBACK_PROVIDER", None),
                ollama=OllamaConfig(
                    enabled=os.getenv("OLLAMA_ENABLED", "true").lower() == "true",
                    base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
                    default_model=os.getenv("OLLAMA_MODEL", "phi3"),
                    timeout=int(os.getenv("OLLAMA_TIMEOUT", "120")),
                    max_retries=int(os.getenv("OLLAMA_MAX_RETRIES", "3"))
                ),
                openai=OpenAIConfig(
                    enabled=os.getenv("OPENAI_ENABLED", "false").lower() == "true",
                    api_key=os.getenv("OPENAI_API_KEY"),
                    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                    default_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                    organization=os.getenv("OPENAI_ORGANIZATION"),
                    timeout=int(os.getenv("OPENAI_TIMEOUT", "120")),
                    max_retries=int(os.getenv("OPENAI_MAX_RETRIES", "3"))
                ),
                github=GitHubModelsConfig(
                    enabled=os.getenv("GITHUB_ENABLED", "false").lower() == "true",
                    api_key=os.getenv("GITHUB_API_KEY"),
                    default_model=os.getenv("GITHUB_MODEL", "gpt-4o"),
                    timeout=int(os.getenv("GITHUB_TIMEOUT", "120")),
                    max_retries=int(os.getenv("GITHUB_MAX_RETRIES", "3"))
                ),
                azure=AzureOpenAIConfig(
                    enabled=os.getenv("AZURE_ENABLED", "false").lower() == "true",
                    api_key=os.getenv("AZURE_API_KEY"),
                    base_url=os.getenv("AZURE_ENDPOINT"),
                    deployment_name=os.getenv("AZURE_DEPLOYMENT_NAME"),
                    api_version=os.getenv("AZURE_API_VERSION", "2024-02-01"),
                    timeout=int(os.getenv("AZURE_TIMEOUT", "120")),
                    max_retries=int(os.getenv("AZURE_MAX_RETRIES", "3"))
                ),
                venice=VeniceAIConfig(
                    enabled=os.getenv("VENICE_ENABLED", "false").lower() == "true",
                    api_key=os.getenv("VENICE_API_KEY"),
                    base_url=os.getenv("VENICE_BASE_URL", "https://api.venice.ai/api/v1"),
                    default_model=os.getenv("VENICE_MODEL", "llama-3.3-70b"),
                    timeout=int(os.getenv("VENICE_TIMEOUT", "120")),
                    max_retries=int(os.getenv("VENICE_MAX_RETRIES", "3")),
                    check_diem_before_request=os.getenv("VENICE_CHECK_DIEM", "true").lower() == "true",
                    diem_warning_threshold=float(os.getenv("VENICE_DIEM_WARNING", "1.0")),
                    diem_critical_threshold=float(os.getenv("VENICE_DIEM_CRITICAL", "0.1")),
                    auto_fallback_on_low_diem=os.getenv("VENICE_AUTO_FALLBACK", "true").lower() == "true"
                )
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
    # All checks passed
    return True
    
    return True