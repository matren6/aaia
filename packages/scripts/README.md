# Application Scripts

This directory contains scripts that are bundled with and run by the AAIA application.

## Purpose
Application runtime tools that are packaged with the application for database management, configuration validation, and application setup.

## Contents

### Database Management
- `migrate.py` - Run database migrations
- `check_migrations.py` - Check migration status

### Configuration Management
- `validate_config.py` - Validate application configuration
- `audit_config.py` - Audit configuration for issues

### Testing
- `wsl_integration_test.sh` - WSL integration testing
- `wsl_quick_test.py` - Quick WSL test
- `test_commands.txt` - Command test batch file

## Usage

### Database Migrations
```bash
# Run migrations on database
python3 packages/scripts/migrate.py data/scribe.db

# Check migration status
python3 packages/scripts/check_migrations.py
```

### Configuration
```bash
# Validate configuration
python3 packages/scripts/validate_config.py

# Audit configuration
python3 packages/scripts/audit_config.py
```

### Testing
```bash
# WSL integration test
bash packages/scripts/wsl_integration_test.sh

# Quick WSL test
python3 packages/scripts/wsl_quick_test.py
```

## Guidelines

- ✅ Use for **application runtime tools**
- ✅ These scripts are **bundled with the package**
- ✅ Can be imported by application code
- ✅ Use LF line endings for `.sh` files
- ❌ Do NOT add development-only utilities (use `/scripts/` instead)

## Related

- **Development Scripts**: See `/scripts/` directory
- **Application Tests**: See `/packages/tests/`
- **Comprehensive Tests**: See `/tests/`
