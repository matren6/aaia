# Application Module Tests

This directory contains unit tests for AAIA application modules (Phase 5+).

## Purpose
Tests for the current generation of application modules, focusing on Phase 5 development and beyond.

## Contents

- `test_phase5_modules.py` - Tests for Phase 5 modules

## Usage

### Run Application Tests Only
```bash
# Run all application module tests
pytest packages/tests/

# Run with verbose output
pytest -v packages/tests/

# Run specific test
pytest packages/tests/test_phase5_modules.py::test_module_name
```

### Run with Other Tests
```bash
# Run all tests (app + legacy)
pytest tests/ packages/tests/

# Run only app tests, stop on first failure
pytest -x packages/tests/
```

## Guidelines

- ✅ Test current module implementations
- ✅ Use pytest framework
- ✅ Test both success and failure cases
- ✅ Mock external dependencies
- ✅ Keep tests fast and isolated
- ❌ Do NOT mix with legacy phase tests (use separate files)

## Test Structure

```python
# Example test structure
import pytest
from packages.modules.my_module import MyModule

class TestMyModule:
    """Test MyModule functionality."""
    
    def setup_method(self):
        """Setup for each test."""
        self.module = MyModule()
    
    def test_successful_operation(self):
        """Test normal operation."""
        result = self.module.do_something()
        assert result is not None
    
    def test_error_handling(self):
        """Test error handling."""
        with pytest.raises(ValueError):
            self.module.bad_operation()
```

## Related

- **All Tests**: See `/tests/`
- **Legacy Tests**: See `/tests/test_*.py` files
- **Test Configuration**: See `/tests/conftest.py`
