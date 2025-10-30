# Error Handling & Retry Strategies (Web API)

Purpose: Define robust error handling for the IBKR Client Portal Web API integration, with clear retry policies and user guidance.

## Error Classification

### 1. Authentication & Session Errors
- **401 Unauthorized**: Session expired or invalid
- **403 Forbidden**: Insufficient permissions or gateway not authenticated
- **Session timeout**: Gateway session expired (daily reset)

**User Action**: Re-authenticate at `https://localhost:5000/` in browser, then retry.

### 2. Network & Connectivity Errors
- **Connection refused**: Gateway not running on localhost:5000
- **TLS errors**: Self-signed certificate issues
- **Timeout**: Request exceeded timeout threshold
- **DNS resolution**: localhost resolution issues

**User Action**: Start gateway, check port availability, verify TLS settings.

### 3. API Errors
- **400 Bad Request**: Invalid parameters or malformed request
- **404 Not Found**: Endpoint not available or account not found
- **429 Too Many Requests**: Rate limiting (rare for local gateway)
- **500 Internal Server Error**: Gateway or IBKR server issues

**User Action**: Check request parameters, retry with backoff, contact support if persistent.

### 4. Data Validation Errors
- **Schema validation**: Missing required fields, invalid data types
- **Business logic**: Negative positions without short flag, impossible P&L
- **Date validation**: Future dates, invalid timestamps

**User Action**: Review data quality, check source data integrity.

## Retry Strategy

### Exponential Backoff Policy
```python
# Base delay: 1 second
# Max delay: 60 seconds
# Max attempts: 5
# Jitter: ±25% random variation
```

### Retryable Errors
- Network timeouts and connection errors
- 5xx server errors
- Rate limiting (429)
- Temporary gateway issues

### Non-Retryable Errors
- 401/403 authentication errors (require re-login)
- 400 bad request (parameter issues)
- 404 not found (endpoint/account issues)
- Data validation errors

### Retry Implementation
```python
def retry_with_backoff(func, max_attempts=5, base_delay=1.0, max_delay=60.0):
    for attempt in range(max_attempts):
        try:
            return func()
        except RetryableError as e:
            if attempt == max_attempts - 1:
                raise
            delay = min(base_delay * (2 ** attempt), max_delay)
            delay *= (0.75 + 0.5 * random.random())  # Jitter
            time.sleep(delay)
        except NonRetryableError as e:
            raise
```

## Error Surfacing

### 1. CLI Output
- **Success**: Green checkmark or "✓" symbol
- **Warning**: Yellow "⚠" with retry count
- **Error**: Red "✗" with clear action message
- **Info**: Blue "ℹ" for non-blocking notes

### 2. Notebook Interface
- **Status Panel**: Real-time error indicators with color coding
- **Error Panel**: Recent errors with timestamps and resolution steps
- **Inline Output**: Error messages in cell output where triggered

### 3. Logging
- **Structured JSON logs** in `data/logs/`
- **Log levels**: DEBUG, INFO, WARN, ERROR
- **Fields**: timestamp, operation, error_code, message, retry_count, account_id (redacted)

## Common Error Scenarios & Messages

### Gateway Not Running
```
Error: Gateway not reachable on https://localhost:5000
Action: Start gateway with ./bin/run.sh root/conf.yaml
```

### Session Expired
```
Error: Session expired (401)
Action: Re-authenticate at https://localhost:5000/, then retry
```

### Invalid Account ID
```
Error: Account not found (404)
Action: Check account ID in configuration
```

### Data Validation Failure
```
Error: Validation failed - negative position without short flag
Action: Review position data for symbol AAPL
```

### Network Timeout
```
Warning: Request timeout (retry 2/5)
Info: Retrying in 3.2 seconds...
```

## Error Recovery Procedures

### 1. Session Recovery
1. Detect 401/403 error
2. Log error with timestamp
3. Display re-authentication prompt
4. Wait for user confirmation
5. Retry original operation

### 2. Gateway Recovery
1. Detect connection refused
2. Check if gateway process is running
3. Provide start command
4. Wait for gateway to be ready
5. Retry operation

### 3. Data Recovery
1. Detect validation errors
2. Log offending records
3. Continue with valid records
4. Report summary of issues
5. Suggest data review

## Monitoring & Alerting

### Error Metrics
- Error rate by type (auth, network, validation)
- Retry success rate
- Average retry delay
- Session expiry frequency

### Health Checks
- Gateway connectivity (`/v1/api/tickle`)
- Session validity
- Data freshness (last sync time)
- Validation pass rate

### Log Analysis
- Parse structured logs for error patterns
- Track error frequency by operation
- Monitor retry effectiveness
- Alert on error rate spikes

## Best Practices

### 1. Graceful Degradation
- Continue processing valid records when some fail
- Provide partial results with error summary
- Maintain operation state for recovery

### 2. User Experience
- Clear, actionable error messages
- Progress indicators for long operations
- Non-blocking error display
- Quick recovery options

### 3. Debugging
- Include request/response details in debug logs
- Preserve error context for troubleshooting
- Use correlation IDs for request tracking
- Log timing information for performance analysis

### 4. Security
- Redact sensitive information in logs
- Don't log full request/response bodies
- Use secure logging practices
- Monitor for suspicious error patterns

## Testing Error Scenarios

### Unit Tests
- Mock various error responses
- Test retry logic with different error types
- Validate error message formatting
- Test exponential backoff calculation

### Integration Tests
- Simulate gateway downtime
- Test session expiry scenarios
- Validate error recovery procedures
- Test data validation edge cases

### End-to-End Tests
- Full error recovery workflows
- User interaction with error messages
- Logging and monitoring verification
- Performance under error conditions

## References
- Web API overview: `docs/ib_web_api.md`
- Authentication guide: `docs/ib_web_api_auth.md`
- Endpoints catalog: `docs/ib_web_api_endpoints.md`
- Notebook UX: `docs/notebook_ux.md`
