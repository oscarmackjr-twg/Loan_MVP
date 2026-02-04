# Testing Guide

This directory contains comprehensive tests for the Loan Engine application.

## Test Structure

```
tests/
├── conftest.py                    # Shared fixtures and test configuration
├── test_date_utils.py             # Date calculation utilities
├── test_file_discovery.py         # File discovery and pattern matching
├── test_normalize.py              # Data normalization
├── test_enrichment.py              # Data enrichment and tagging
├── test_rules_purchase_price.py   # Purchase price validation
├── test_rules_underwriting.py     # Underwriting validation
├── test_rules_eligibility.py      # Eligibility checks
├── test_integration_pipeline.py   # Pipeline integration tests
├── test_api_routes.py             # API endpoint tests
└── README.md                       # This file
```

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test File

```bash
pytest tests/test_date_utils.py
```

### Run Specific Test Class

```bash
pytest tests/test_date_utils.py::TestCalculateNextTuesday
```

### Run Specific Test Function

```bash
pytest tests/test_date_utils.py::TestCalculateNextTuesday::test_next_tuesday_from_monday
```

### Run with Coverage

```bash
pytest --cov=backend --cov-report=html
```

### Run with Verbose Output

```bash
pytest -v
```

### Run with Print Statements

```bash
pytest -s
```

## Test Categories

### Unit Tests

- **Date Utilities**: Test date calculation functions
- **File Discovery**: Test file pattern matching and discovery
- **Normalization**: Test data cleaning and standardization
- **Enrichment**: Test data enrichment and tagging
- **Validation Rules**: Test purchase price, underwriting, CoMAP, and eligibility checks

### Integration Tests

- **Pipeline Execution**: Test end-to-end pipeline runs
- **API Endpoints**: Test REST API functionality
- **Database Operations**: Test data persistence

## Test Fixtures

### Database Fixtures

- `test_db_engine`: In-memory SQLite database engine
- `test_db_session`: Database session for tests
- `override_get_db`: Dependency override for FastAPI

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

- `temp_dir`: Temporary directory for file operations
- `sample_input_dir`: Sample input directory structure

## Writing New Tests

### Example Unit Test

```python
def test_my_function():
    """Test description."""
    # Arrange
    input_data = create_test_data()

    # Act
    result = my_function(input_data)

    # Assert
    assert result == expected_output
```

### Example Integration Test

```python
def test_api_endpoint(client, auth_headers):
    """Test API endpoint."""
    response = client.get("/api/endpoint", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["key"] == "value"
```

## Test Data

Test data is created using fixtures in `conftest.py`. For complex scenarios, create additional fixtures or use factories.

## Mocking

Use `pytest.mock` for mocking external dependencies:

```python
from unittest.mock import patch

@patch('module.external_function')
def test_with_mock(mock_func):
    mock_func.return_value = "mocked"
    # Test code
```

## Best Practices

1. **Test Isolation**: Each test should be independent
2. **Clear Names**: Use descriptive test function names
3. **Arrange-Act-Assert**: Follow AAA pattern
4. **One Assertion Per Test**: Focus each test on one behavior
5. **Use Fixtures**: Reuse common setup via fixtures
6. **Test Edge Cases**: Include boundary conditions
7. **Test Error Cases**: Verify error handling

## Continuous Integration

Tests should pass in CI/CD pipeline. Ensure:

- All tests pass locally
- No hardcoded paths or credentials
- Tests are deterministic
- Database fixtures use in-memory SQLite

## Coverage Goals

- **Unit Tests**: 80%+ coverage
- **Integration Tests**: All critical paths
- **E2E Tests**: At least 3 scenarios

## Troubleshooting

### Tests Failing

1. Check test database setup
2. Verify fixtures are loading correctly
3. Check for hardcoded paths
4. Verify dependencies are installed

### Slow Tests

1. Use in-memory database
2. Minimize file I/O
3. Use fixtures efficiently
4. Consider test parallelization

### Flaky Tests

1. Ensure test isolation
2. Check for race conditions
3. Verify mock setup
4. Check date/time dependencies
