# Testing Plan (Web API, macOS-local)

Purpose: Define comprehensive testing strategy for the IBKR Client Portal Web API integration, covering unit, integration, and end-to-end testing.

## Testing Strategy Overview

- **Test-driven development**: Write tests before implementation where possible
- **Mock external dependencies**: Use mocks for gateway and API responses
- **Local testing only**: No external API calls during testing
- **Data validation focus**: Emphasize data quality and business logic validation
- **Error scenario coverage**: Test all error handling paths

## Test Structure

```
tests/
├── unit/
│   ├── test_api_client.py
│   ├── test_data_normalization.py
│   ├── test_validation.py
│   └── test_retry_logic.py
├── integration/
│   ├── test_gateway_integration.py
│   ├── test_database_operations.py
│   └── test_sync_workflows.py
├── fixtures/
│   ├── sample_responses.py
│   ├── mock_gateway.py
│   └── test_data.py
└── conftest.py
```

## Unit Tests

### API Client Tests (`test_api_client.py`)
- **Session management**: Cookie handling, session expiry detection
- **Request building**: URL construction, parameter encoding
- **Response parsing**: JSON parsing, error detection
- **Retry logic**: Exponential backoff, retryable vs non-retryable errors
- **TLS handling**: Self-signed certificate acceptance

### Data Normalization Tests (`test_data_normalization.py`)
- **Response mapping**: API responses → pandas DataFrames
- **Data type validation**: Correct dtypes, nullable fields
- **Field extraction**: Required vs optional fields
- **Data cleaning**: Null handling, string normalization
- **Schema validation**: Required fields, enum values

### Validation Tests (`test_validation.py`)
- **Balance reconciliation**: Cash + positions ≈ account value
- **Position consistency**: Negative quantities, currency validation
- **Trade validation**: Side validation, price ranges, quantity checks
- **Date validation**: Future date detection, timestamp ordering
- **Outlier detection**: P&L anomaly detection

### Retry Logic Tests (`test_retry_logic.py`)
- **Exponential backoff**: Delay calculation, jitter application
- **Error classification**: Retryable vs non-retryable errors
- **Max attempts**: Retry limit enforcement
- **Circuit breaker**: Failure threshold handling

## Integration Tests

### Gateway Integration Tests (`test_gateway_integration.py`)
- **Connection testing**: Gateway availability, port binding
- **Authentication flow**: Login process, session establishment
- **Endpoint access**: All required endpoints accessible
- **Error handling**: Gateway downtime, session expiry
- **TLS verification**: Certificate handling

### Database Operations Tests (`test_database_operations.py`)
- **Schema creation**: Alembic migrations, table creation
- **Data insertion**: Upsert operations, constraint validation
- **Query operations**: Data retrieval, filtering, aggregation
- **Transaction handling**: Rollback on errors, commit success
- **Encryption**: SQLCipher encryption/decryption

### Sync Workflow Tests (`test_sync_workflows.py`)
- **Incremental sync**: Cursor management, overlap handling
- **Idempotency**: Duplicate record handling
- **Error recovery**: Partial failure handling
- **Data consistency**: Cross-table relationships
- **Performance**: Large dataset handling

## Test Fixtures

### Sample Responses (`fixtures/sample_responses.py`)
```python
SAMPLE_ACCOUNTS = [
    {"accountId": "U1234567", "accountTitle": "Individual", "currency": "USD"}
]

SAMPLE_POSITIONS = [
    {
        "conid": 265598,
        "symbol": "AAPL",
        "secType": "STK",
        "position": 100,
        "marketPrice": 150.25,
        "marketValue": 15025.00,
        "currency": "USD"
    }
]

SAMPLE_EXECUTIONS = [
    {
        "execId": "1234.5678",
        "orderId": 987654321,
        "time": "2025-10-29T14:30:00Z",
        "conid": 265598,
        "symbol": "AAPL",
        "side": "BUY",
        "shares": 100,
        "price": 150.00,
        "currency": "USD"
    }
]
```

### Mock Gateway (`fixtures/mock_gateway.py`)
```python
class MockGateway:
    def __init__(self):
        self.authenticated = False
        self.responses = {}
    
    def authenticate(self):
        self.authenticated = True
    
    def get_response(self, endpoint):
        return self.responses.get(endpoint, {})
    
    def set_response(self, endpoint, response):
        self.responses[endpoint] = response
```

### Test Data (`fixtures/test_data.py`)
- **Valid data**: Complete, properly formatted test data
- **Invalid data**: Malformed, missing fields, wrong types
- **Edge cases**: Empty responses, null values, extreme values
- **Error responses**: Various HTTP error codes and messages

## Test Configuration

### pytest Configuration (`conftest.py`)
```python
import pytest
from fixtures.mock_gateway import MockGateway

@pytest.fixture
def mock_gateway():
    return MockGateway()

@pytest.fixture
def sample_accounts():
    return SAMPLE_ACCOUNTS

@pytest.fixture
def sample_positions():
    return SAMPLE_POSITIONS
```

### Test Environment Setup
- **Python version**: 3.11+
- **Dependencies**: pytest, pandas, requests-mock
- **Database**: In-memory SQLite for testing
- **Mocking**: requests-mock for HTTP calls
- **Coverage**: pytest-cov for coverage reporting

## Test Scenarios

### Happy Path Scenarios
1. **Successful sync**: All endpoints return valid data
2. **Partial sync**: Some endpoints fail, others succeed
3. **Data validation**: All data passes validation checks
4. **Error recovery**: Retry succeeds after initial failure
5. **Session management**: Session maintained across requests

### Error Scenarios
1. **Gateway unavailable**: Connection refused, timeout
2. **Session expired**: 401/403 responses
3. **Invalid data**: Malformed responses, missing fields
4. **Network issues**: Intermittent connectivity problems
5. **Validation failures**: Business logic violations

### Edge Cases
1. **Empty responses**: No data returned
2. **Large datasets**: Performance with many records
3. **Concurrent access**: Multiple sync operations
4. **Resource limits**: Memory and disk usage
5. **Unicode handling**: Special characters in data

## Test Data Management

### Test Database
- **In-memory SQLite**: Fast, isolated tests
- **Schema creation**: Apply migrations for each test
- **Data cleanup**: Reset database between tests
- **Encryption testing**: Test with SQLCipher

### Mock Data
- **Realistic data**: Use actual IBKR response formats
- **Varied scenarios**: Different account types, positions
- **Error cases**: Invalid data, missing fields
- **Performance data**: Large datasets for stress testing

## Performance Testing

### Load Testing
- **Concurrent requests**: Multiple simultaneous API calls
- **Large datasets**: Thousands of positions, executions
- **Memory usage**: Monitor memory consumption
- **Response times**: API call latency measurement

### Stress Testing
- **Resource limits**: Memory, disk, CPU usage
- **Error handling**: Behavior under stress
- **Recovery**: System recovery after stress
- **Data integrity**: Data consistency under load

## Security Testing

### Authentication Testing
- **Session management**: Cookie handling, expiry
- **Credential security**: No credential storage
- **TLS verification**: Certificate handling
- **Access control**: Localhost-only access

### Data Security Testing
- **Encryption**: Database encryption verification
- **Redaction**: Log data redaction
- **Access logging**: Audit trail verification
- **Backup security**: Encrypted backup testing

## Test Automation

### Continuous Integration
- **Pre-commit hooks**: Run tests before commit
- **Pull request checks**: Automated test runs
- **Coverage reporting**: Track test coverage
- **Performance monitoring**: Track test execution time

### Test Execution
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/unit/test_api_client.py

# Run with verbose output
pytest -v

# Run integration tests only
pytest tests/integration/
```

## Test Reporting

### Coverage Metrics
- **Line coverage**: Minimum 90% line coverage
- **Branch coverage**: Minimum 80% branch coverage
- **Function coverage**: 100% function coverage
- **Critical path coverage**: 100% critical path coverage

### Test Reports
- **HTML reports**: pytest-html for detailed reports
- **Coverage reports**: Coverage.py HTML reports
- **Performance reports**: Execution time tracking
- **Error reports**: Detailed error logging

## Test Maintenance

### Test Updates
- **API changes**: Update mocks when API changes
- **Schema changes**: Update test data for schema changes
- **New features**: Add tests for new functionality
- **Bug fixes**: Add regression tests for fixed bugs

### Test Documentation
- **Test descriptions**: Clear test purpose and scope
- **Setup instructions**: How to run tests
- **Troubleshooting**: Common test issues and solutions
- **Best practices**: Testing guidelines and standards

## Entry and Exit Criteria

### Entry Criteria
- [ ] Code completion for feature being tested
- [ ] Test environment setup complete
- [ ] Test data prepared
- [ ] Mock services configured
- [ ] Test cases written and reviewed

### Exit Criteria
- [ ] All critical tests passing
- [ ] Coverage targets met
- [ ] Performance requirements satisfied
- [ ] Security tests passing
- [ ] Documentation updated

## References
- Web API overview: `docs/ib_web_api.md`
- Data model: `docs/data_model.md`
- Error handling: `docs/error_handling_retry.md`
- Security measures: `docs/security_measures.md`
- Implementation checklist: `docs/implementation_checklist.md`
