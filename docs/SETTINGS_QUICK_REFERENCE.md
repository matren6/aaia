# Runtime Settings Management - Quick Reference

## Commands

### View All Settings
```bash
config
```
Shows all configuration with hierarchical display.

### Get Specific Setting
```bash
config get llm.default_provider
config get database.timeout
config get economics.initial_balance
config get evolution.safety_mode
```

### Set Setting Value
```bash
# String
config set llm.default_provider openai

# Integer
config set database.timeout 60

# Float
config set economics.initial_balance 500.0

# Boolean
config set evolution.safety_mode false
config set scheduler.enabled true
```

## Common Settings

### LLM Providers
- `llm.default_provider` - Primary: ollama, openai, github, azure, venice
- `llm.fallback_provider` - Secondary if primary unavailable
- `llm.ollama.enabled` - Enable/disable Ollama
- `llm.ollama.default_model` - Ollama model (default: phi3)
- `llm.openai.enabled` - Enable/disable OpenAI

### Economics
- `economics.initial_balance` - Starting balance
- `economics.low_balance_threshold` - Alert threshold
- `economics.inference_cost` - Cost per inference
- `economics.income_generation_enabled` - Enable income generation

### Evolution
- `evolution.safety_mode` - Enable safety checks
- `evolution.max_retries` - Max retry attempts
- `evolution.backup_before_modify` - Backup before changes

### Database
- `database.timeout` - Query timeout (seconds)
- `database.backup_enabled` - Enable backups
- `database.path` - Database file path

### Scheduler
- `scheduler.enabled` - Enable scheduler
- `scheduler.diagnosis_interval` - Diagnosis interval (seconds)
- `scheduler.task_timeout` - Task timeout (seconds)

## Usage Tips

### View Before Changing
```bash
config get database.timeout
config set database.timeout 60
config get database.timeout
```

### Boolean Values
```bash
# These are all equivalent for true:
config set evolution.safety_mode true
config set evolution.safety_mode 1
config set evolution.safety_mode yes
config set evolution.safety_mode enabled

# These are all equivalent for false:
config set evolution.safety_mode false
config set evolution.safety_mode 0
config set evolution.safety_mode no
config set evolution.safety_mode disabled
```

### Nested Settings
```bash
# Provider-specific settings use nested paths
config get llm.ollama.base_url
config get llm.openai.api_key
config get llm.venice.diem_warning_threshold
```

## Important Notes

⚠️ **Changes are in-memory only** - Lost on restart  
💾 **To persist changes** - Edit .env file and restart  
✅ **Type safe** - Automatic type conversion  
🔍 **Path validation** - Clear errors for invalid keys  

## Error Messages

### Type Error
```
Error: Invalid value for setting 'database.timeout': invalid literal for int() with base 10: 'not_a_number'
Please provide a valid int
```

### Setting Not Found
```
Error: Setting not found: invalid.key
Available settings can be viewed with 'config' command
```

## Help
```bash
help
```
Shows all available commands including config.

## Testing Batch Commands
```bash
# Create scripts/test.txt with commands:
config get llm.default_provider
config set llm.default_provider openai
config get llm.default_provider

# Run:
PYTHONPATH=packages python3 packages/main.py --cmd-file scripts/test.txt --autoexit
```

---

For full documentation, see `docs/RUNTIME_SETTINGS_MANAGEMENT.md`
