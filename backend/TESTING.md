# Testing Strategy and Guide

## Overview

This document outlines the comprehensive testing strategy for the Loan Engine application, including unit tests, integration tests, and end-to-end tests.

## Test Structure

```
backend/tests/
├── conftest.py                    # Shared fixtures and configuration
├── test_date_utils.py             # Date calculation tests
├── test_file_discovery.py         # File discovery tests
├── test_normalize.py              # Data normalization tests
├── test_enrichment.py             # Data enrichment tests
├── test_rules_purchase_price.py   # Purchase price validation tests
├── test_rules_underwriting.py     # Underwriting validation tests
├── test_rules_eligibility.py      # Eligibility check tests
├── test_integration_pipeline.py   # Pipeline integration tests
├── test_api_routes.py             # API endpoint tests
└── README.md                      # Test documentation
```

## Test Categories

### 1. Unit Tests

**Purpose**: Test individual functions and components in isolation.

**Coverage**:

- ✅ Date calculation utilities (next Tuesday, yesterday, last month end)
- ✅ File discovery and pattern matching
- ✅ Data normalization (SFY, Prime, loans)
- ✅ Data enrichment (tagging, seller loan numbers, repurchase detection)
- ✅ Purchase price validation
- ✅ Underwriting validation
- ✅ CoMAP validation
- ✅ Eligibility checks (Prime and SFY)

**Location**: `tests/test_*.py` (except integration tests)

**Run**: `pytest tests/test_date_utils.py`

### 2. Integration Tests

**Purpose**: Test component interactions and data flow.

**Coverage**:

- ✅ Full pipeline execution
- ✅ Database persistence
- ✅ Excel export generation
- ✅ Exception collection and reporting

**Location**: `tests/test_integration_*.py`

**Run**: `pytest tests/test_integration_pipeline.py`

### 3. API Tests

**Purpose**: Test REST API endpoints and authentication.

**Coverage**:

- ✅ Health check endpoint
- ✅ Authentication and authorization
- ✅ Run creation and retrieval
- ✅ Exception retrieval
- ✅ Sales team data isolation

**Location**: `tests/test_api_*.py`

**Run**: `pytest tests/test_api_routes.py`

## Running Tests

### Prerequisites

```bash
# Install test dependencies
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov
```

### Basic Commands

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend --cov-report=html

# Run specific test file
pytest tests/test_date_utils.py

# Run specific test class
pytest tests/test_date_utils.py::TestCalculateNextTuesday

# Run specific test function
pytest tests/test_date_utils.py::TestCalculateNextTuesday::test_next_tuesday_from_monday

# Run with verbose output
pytest -v

# Run with print statements
pytest -s

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration
```

## Test Fixtures

### Database Fixtures

- `test_db_engine`: In-memory SQLite database
- `test_db_session`: Database session for tests
- `override_get_db`: FastAPI dependency override

### Data Fixtures

- `sample_loans_df`: Sample loans dataframe
- `sample_sfy_df`: Sample SFY dataframe
- `sample_prime_df`: Sample Prime dataframe
- `sample_buy_df`: Combined buy dataframe
- `sample_loans_types_df`: Loan types master sheet
- `sample_underwriting_df`: Underwriting grid
- `sample_comap_df`: CoMAP grid
- `sample_existing_file`: Existing assets file

### User Fixtures

- `sample_sales_team`: Test sales team
- `sample_admin_user`: Admin user
- `sample_sales_user`: Sales team user

### File System Fixtures

- `temp_dir`: Temporary directory
- `sample_input_dir`: Sample input directory structure

## Test Coverage Goals

### Current Status

- **Unit Tests**: Comprehensive coverage of core functions
- **Integration Tests**: Pipeline execution and database operations
- **API Tests**: Authentication and endpoint functionality

### Target Coverage

- **Unit Tests**: 80%+ code coverage
- **Integration Tests**: All critical paths
- **E2E Tests**: At least 3 complete scenarios

## Writing New Tests

### Unit Test Template

```python
def test_function_name():
    """Test description."""
    # Arrange
    input_data = create_test_data()
    expected_output = create_expected_data()

    # Act
    result = function_under_test(input_data)

    # Assert
    assert result == expected_output
    assert len(result) == expected_length
```

### Integration Test Template

```python
def test_integration_scenario(test_db_session, sample_data):
    """Test integration scenario."""
    # Setup
    context = create_test_context()

    # Execute
    with PipelineExecutor(context) as executor:
        result = executor.execute(test_folder)

    # Verify
    assert result['status'] == 'completed'
    verify_database_state(test_db_session)
```

### API Test Template

```python
def test_api_endpoint(client, auth_headers):
    """Test API endpoint."""
    # Execute
    response = client.get("/api/endpoint", headers=auth_headers)

    # Verify
    assert response.status_code == 200
    assert response.json()["key"] == "value"
```

## Test Data Management

### Creating Test Data

1. **Use Fixtures**: Reuse common data via fixtures in `conftest.py`
2. **Factories**: Create complex data using factory functions
3. **Mocking**: Mock external dependencies when needed

### Test Data Isolation

- Each test uses isolated database session
- Temporary directories are cleaned up automatically
- No shared state between tests

## Best Practices

### 1. Test Isolation

- Each test should be independent
- No shared state between tests
- Clean up after each test

### 2. Clear Test Names

- Use descriptive function names
- Follow pattern: `test_<what>_<condition>_<expected_result>`

### 3. Arrange-Act-Assert

- **Arrange**: Set up test data
- **Act**: Execute function under test
- **Assert**: Verify results

### 4. One Assertion Per Test

- Focus each test on one behavior
- Use multiple assertions only when testing related properties

### 5. Use Fixtures

- Reuse common setup via fixtures
- Avoid duplicating setup code

### 6. Test Edge Cases

- Boundary conditions
- Empty inputs
- Null/None values
- Invalid inputs

### 7. Test Error Cases

- Verify error handling
- Check exception messages
- Validate error responses

## Continuous Integration

### CI Configuration

Tests should run automatically in CI/CD pipeline:

```yaml
# Example GitHub Actions
- name: Run tests
  run: |
    pytest --cov=backend --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v2
```

### Requirements

- All tests must pass
- No hardcoded paths or credentials
- Tests must be deterministic
- Use in-memory database for speed

## Troubleshooting

### Common Issues

1. **Import Errors**

   - Check Python path
   - Verify package installation
   - Check `__init__.py` files

2. **Database Errors**

   - Verify test database setup
   - Check fixture initialization
   - Ensure proper cleanup

3. **File Path Issues**

   - Use temporary directories
   - Avoid hardcoded paths
   - Check path separators (Windows vs Unix)

4. **Mock Issues**
   - Verify mock setup
   - Check patch paths
   - Ensure proper cleanup

### Debugging Tips

1. **Use `pytest -s`**: See print statements
2. **Use `pytest -v`**: Verbose output
3. **Use `pytest --pdb`**: Drop into debugger on failure
4. **Check fixtures**: Verify fixture data
5. **Isolate test**: Run single test to debug

## Performance Considerations

### Fast Tests

- Use in-memory database
- Minimize file I/O
- Use fixtures efficiently
- Mock external services

### Slow Tests

- Mark with `@pytest.mark.slow`
- Run separately: `pytest -m "not slow"`
- Consider parallelization: `pytest -n auto`

## Future Enhancements

### Planned Additions

1. **E2E Tests**: Full user workflow tests
2. **Performance Tests**: Load and stress testing
3. **Security Tests**: Authentication and authorization edge cases
4. **Contract Tests**: API contract validation
5. **Visual Regression**: UI component tests (if applicable)

### Test Automation

1. **Pre-commit Hooks**: Run tests before commit
2. **Nightly Runs**: Full test suite
3. **Coverage Reports**: Track coverage trends
4. **Test Reports**: Generate HTML reports

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Testing Best Practices](https://docs.python.org/3/library/unittest.html)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
