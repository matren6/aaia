# Test Suite

This directory contains the test suite for the AAIA application.

## Purpose
Comprehensive tests for the AAIA application including unit tests, integration tests, and phase-specific tests.

## Structure

### Test Files

#### Legacy/Phase Tests (Root)
- `test_evolution.py` - Evolution system tests
- `test_scheduler_execution.py` - Scheduler execution tests
- `test_venice_live.py` - Venice provider integration tests
- `conftest.py` - Pytest configuration and fixtures

#### Current Module Tests (packages/)
- `packages/tests/test_phase5_modules.py` - Phase 5 module tests

## Usage

### Run All Tests
```bash
# Using pytest
pytest tests/ packages/tests/

# With verbose output
pytest -v tests/ packages/tests/

# With coverage
pytest --cov=packages tests/ packages/tests/
```

### Run Specific Test
```bash
# Run specific test file
pytest tests/test_scheduler_execution.py

# Run specific test
pytest tests/test_scheduler_execution.py::test_scheduler_starts

# Run with specific marker
pytest -m integration tests/
```

### Run with Options
```bash
# Show output (don't capture)
pytest -s tests/

# Run only failed tests
pytest --lf tests/

# Run failed tests first, then others
pytest --ff tests/

# Stop on first failure
pytest -x tests/

# Run N tests at a time (parallel)
pytest -n 4 tests/
```

## Guidelines

- ✅ Use pytest as test framework
- ✅ Put unit tests in `/tests/` or `/packages/tests/`
- ✅ Put integration tests in `/tests/integration/` (when created)
- ✅ Use `conftest.py` for shared fixtures
- ✅ Name test files `test_*.py`
- ✅ Name test functions `test_*`
- ❌ Do NOT add development tools here (use `/scripts/`)

## Test Categories

### Unit Tests
- Isolated component testing
- Fast execution
- No external dependencies
- Location: `/tests/unit/` or `/packages/tests/`

### Integration Tests
- Multiple components together
- May have external dependencies
- Slower execution
- Location: `/tests/integration/`

### Phase Tests
- Phase-specific testing
- May be deprecated or archived
- Location: `/tests/phase/` or `/tests/`

## Configuration

See `conftest.py` for:
- Pytest fixtures
- Test configuration
- Test markers
- Common test utilities

## Related

- **Development Scripts**: See `/scripts/`
- **Application Scripts**: See `/packages/scripts/`
