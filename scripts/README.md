# Development Scripts

This directory contains development utilities, testing tools, and debugging scripts.

## Purpose
Development-only tools for building, testing, and debugging the AAIA application. These scripts are **NOT** part of the packaged application.

## Contents

### Testing Scripts
- `dry_run_test.sh` - 30-minute autonomous system test
- `monitor_dry_run.sh` - Monitor dry run test execution
- `test_systems.py` - System component test
- `test_tasks_api.py` - Tasks API test
- `test_task_structure.py` - Task structure validation
- `test_scribe_init.py` - Scribe initialization test

### Database & Schema Tools
- `verify_database.py` - Database schema verification and initialization
- `check_schema.py` - Database schema inspection
- `check_db_logs.py` - Database log viewer
- `quick_check_logs.py` - Quick log check utility
- `analyze_logs.py` - Log analysis utility

### Build & Development
- `build.sh` - Build script
- `deploy.sh` - Deployment script
- `dev.sh` - Development environment setup
- `wsl_test.sh` - WSL integration test helper

## Usage

### Running Tests
```bash
# 30-minute dry run test
./scripts/dry_run_test.sh

# Quick system test
python3 scripts/test_systems.py

# Verify database
python3 scripts/verify_database.py
```

### Checking Database
```bash
# View database schema
python3 scripts/check_schema.py data/scribe.db

# View recent logs
python3 scripts/check_db_logs.py data/scribe.db

# Analyze logs
python3 scripts/analyze_logs.py data/scribe.db
```

### WSL Testing
```bash
# Run WSL test
./scripts/wsl_test.sh -c status -e
```

## Guidelines

- ✅ Use for **development and testing**
- ✅ Add new test utilities here
- ✅ Use LF line endings for `.sh` files
- ❌ Do NOT add production runtime scripts (use `/packages/scripts/` instead)
- ❌ Do NOT import into application code

## Related

- **Application Scripts**: See `/packages/scripts/`
- **Tests**: See `/tests/` directory
- **Application Tests**: See `/packages/tests/`
