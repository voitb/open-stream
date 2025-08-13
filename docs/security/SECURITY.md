# Security Documentation

## Overview

This document outlines the comprehensive security enhancements implemented in the Open Stream application to protect against common attack vectors and ensure safe operation of the AI-powered streaming backend.

## Table of Contents

1. [Security Enhancements Overview](#security-enhancements-overview)
2. [Electron Sandbox Configuration](#electron-sandbox-configuration)
3. [Input Validation](#input-validation)
4. [Subprocess Security](#subprocess-security)
5. [Authentication & Authorization](#authentication--authorization)
6. [CORS Policy](#cors-policy)
7. [Rate Limiting](#rate-limiting)
8. [Security Headers](#security-headers)
9. [Security Best Practices](#security-best-practices)
10. [Security Checklist](#security-checklist)
11. [Monitoring and Logging](#monitoring-and-logging)
12. [Threat Model](#threat-model)

## Security Enhancements Overview

### Critical Security Issues Fixed

1. **Command Injection Prevention** - Implemented secure subprocess execution with path validation
2. **Input Sanitization** - Comprehensive Pydantic validation models with XSS/injection protection
3. **Electron Sandbox** - Enabled sandbox mode with context isolation
4. **Authentication** - Token-based authentication for critical endpoints
5. **Rate Limiting** - Protection against DoS and brute-force attacks
6. **Origin Validation** - Strict CORS policy with Electron app ID verification
7. **Security Headers** - Added comprehensive security headers
8. **Secure Logging** - Privacy-compliant logging with sensitive data filtering

### Defense-in-Depth Approach

The security implementation follows a defense-in-depth strategy with multiple layers:
- **Perimeter Defense**: CORS, origin validation, rate limiting
- **Application Layer**: Input validation, authentication, secure APIs
- **Process Isolation**: Electron sandbox, secure subprocess execution
- **Data Protection**: Input sanitization, secure logging, token rotation
- **Monitoring**: Security logging, request tracking, anomaly detection

## Electron Sandbox Configuration

### Configuration Details

```typescript
webPreferences: {
  preload: join(__dirname, '../preload/index.js'),
  sandbox: true,                // Enable sandbox mode
  contextIsolation: true,       // Isolate contexts
  nodeIntegration: false,       // Disable Node.js integration
  webSecurity: true            // Enable web security
}
```

### Security Benefits

- **Process Isolation**: Renderer process runs in a restricted environment
- **Context Isolation**: Prevents script injection between contexts
- **API Control**: Only exposed APIs available through preload script
- **Memory Protection**: Reduces attack surface and prevents privilege escalation

### Implementation Notes

- All backend communication goes through secure IPC channels
- No direct Node.js access from renderer process
- Preload script acts as a secure bridge between contexts
- External link handling redirected to system browser

## Input Validation

### Pydantic Models

Comprehensive validation models implemented for all API endpoints:

#### TextAnalysisRequest Model
```python
class TextAnalysisRequest(BaseModel):
    text: constr(min_length=1, max_length=10000, strip_whitespace=True)
    language: SupportedLanguage = SupportedLanguage.AUTO
    mode: AnalysisMode = AnalysisMode.BASIC
    include_sentiment: bool = True
    include_toxicity: bool = True
    # ... additional fields with validation
```

### Validation Rules

1. **Text Content Validation**:
   - Length limits: 1-10,000 characters
   - HTML escaping to prevent XSS
   - Control character filtering
   - UTF-8 encoding validation
   - Suspicious pattern detection

2. **Username Validation**:
   - Alphanumeric characters plus underscore/hyphen only
   - Length limits: 2-50 characters
   - Reserved name protection
   - Pattern validation: `^[a-zA-Z0-9_\-]+$`

3. **Chat Message Validation**:
   - Length limits: 1-500 characters
   - Spam pattern detection
   - Excessive repetition prevention
   - URL shortener detection

### Protection Against Injection Attacks

#### XSS Prevention Patterns
```python
XSS_PATTERNS = [
    r'<script[^>]*>.*?</script>',  # Script tags
    r'javascript\s*:',            # JavaScript protocols
    r'data\s*:\s*text/html',      # Data URLs with HTML
    r'on\w+\s*=',                # Event handlers
    r'expression\s*\(',          # CSS expressions
]
```

#### SQL Injection Prevention Patterns
```python
SQL_INJECTION_PATTERNS = [
    r'union\s+select',
    r'drop\s+table',
    r'delete\s+from',
    r'--\s*$',                   # SQL comments
    r'/\*.*\*/',                 # SQL block comments
]
```

#### Command Injection Prevention Patterns
```python
COMMAND_INJECTION_PATTERNS = [
    r';\s*(ls|dir|cat|type|echo)',
    r'\|\s*(ls|dir|cat|type|echo)',
    r'`[^`]+`',                  # Backtick substitution
    r'\$\([^)]+\)',              # Command substitution
]
```

## Subprocess Security

### Python Path Validation

Secure Python executable discovery and validation:

```typescript
private getAllowedPythonPaths(): string[] {
  const basePaths = process.platform === 'win32'
    ? [
        'C:\\Python312\\python.exe',
        'C:\\Python311\\python.exe',
        // ... more allowed paths
      ]
    : [
        '/usr/bin/python3',
        '/usr/local/bin/python3',
        '/opt/homebrew/bin/python3',
        // ... more allowed paths
      ]
  
  return basePaths
}
```

### Security Measures

1. **Path Allowlisting**: Only predefined Python paths are allowed
2. **Absolute Path Requirement**: Relative paths are rejected
3. **Version Validation**: Python 3.8+ requirement enforced
4. **Executable Verification**: Confirms valid Python executable
5. **Environment Isolation**: Secure environment variables only

### Command Injection Prevention

- **execFile Instead of exec**: Prevents shell interpretation
- **Argument Array**: Arguments passed as array, not concatenated string
- **Shell Disabled**: `shell: false` prevents shell access
- **Timeout Protection**: Commands have execution timeouts
- **Output Limits**: Maximum output buffer size enforced

### Process Isolation

```typescript
this.serverProcess = spawn(this.pythonPath, [scriptPath, this.port.toString()], {
  cwd: path.dirname(scriptPath),
  env: secureEnv,
  shell: false,              // Never use shell
  stdio: ['ignore', 'pipe', 'pipe'],
  detached: false           // Keep attached to parent
})
```

## Authentication & Authorization

### Shutdown Endpoint Authentication

The shutdown endpoint is protected with token-based authentication:

```python
def validate_shutdown_auth(
    x_shutdown_token: Optional[str] = Header(None),
    x_electron_app_id: Optional[str] = Header(None)
) -> bool:
    if not SHUTDOWN_TOKEN:
        return False
    
    if x_shutdown_token != SHUTDOWN_TOKEN:
        security_logger.critical(f"Invalid shutdown token attempt")
        return False
    
    return True
```

### Token Management

1. **Secure Token Generation**: 64-character hex tokens using crypto.randomBytes
2. **Token Rotation**: Automatic rotation every 30 minutes
3. **Environment Variables**: Tokens stored in secure environment variables
4. **Request Headers**: Tokens passed via `X-Shutdown-Token` header

### Electron App ID Verification

- Unique app identifier: `electron-${process.pid}-${Date.now()}`
- Passed via `X-Electron-App-ID` header
- Additional validation layer for shutdown requests

## CORS Policy

### Origin Validation

Strict CORS configuration with Electron-specific origins:

```python
ALLOWED_ELECTRON_ORIGINS = []
if ELECTRON_APP_ID:
    for port_range in range(50000, 60000):
        ALLOWED_ELECTRON_ORIGINS.extend([
            f"http://localhost:{port_range}",
            f"http://127.0.0.1:{port_range}"
        ])
    ALLOWED_ELECTRON_ORIGINS.append("file://")
```

### CORS Configuration

- **Allowed Origins**: Specific localhost ports + file:// protocol
- **Allowed Methods**: Limited to necessary HTTP methods
- **Allowed Headers**: Specific headers for security and functionality
- **Credentials**: Disabled by default for security
- **Max Age**: 10-minute preflight cache

### Request Filtering

```python
def validate_origin(request: Request) -> bool:
    origin = request.headers.get("origin")
    
    if not origin:
        return True  # Allow direct API calls
    
    # Validate against allowed origins
    if origin in ALLOWED_ELECTRON_ORIGINS:
        return True
    
    # Pattern matching for localhost
    if origin.startswith("http://localhost:") or origin.startswith("http://127.0.0.1:"):
        return True
    
    return False
```

## Rate Limiting

### Implementation

Simple in-memory rate limiter with IP-based tracking:

```python
class RateLimiter:
    def is_allowed(self, client_id: str, max_requests: int = 100) -> bool:
        current_time = datetime.now()
        
        # Check if IP is temporarily blocked
        if client_id in self.blocked_ips:
            if current_time < self.blocked_ips[client_id]:
                return False
        
        # Count recent requests
        # Block IP for 1 minute if limit exceeded
        # ...
```

### Configuration

- **Requests Per Minute**: 100 requests per IP
- **Burst Limit**: 20 requests in quick succession
- **Window**: 60-second sliding window
- **Blocking**: 1-minute temporary IP block for violations
- **Headers**: Rate limit information in response headers

### Monitoring

- Request counts tracked per IP address
- Violations logged to security log
- Rate limit remaining exposed in response headers

## Security Headers

### HTTP Security Headers

All responses include comprehensive security headers:

```python
response.headers["X-Request-ID"] = request_id
response.headers["X-Content-Type-Options"] = "nosniff"
response.headers["X-Frame-Options"] = "DENY"
response.headers["X-XSS-Protection"] = "1; mode=block"
```

### Header Details

1. **X-Content-Type-Options: nosniff**
   - Prevents MIME type sniffing attacks
   - Forces browsers to respect declared content types

2. **X-Frame-Options: DENY**
   - Prevents clickjacking attacks
   - Disallows embedding in frames/iframes

3. **X-XSS-Protection: 1; mode=block**
   - Enables browser XSS filtering
   - Blocks pages when XSS detected

4. **X-Request-ID**
   - Unique request tracking identifier
   - Aids in security monitoring and debugging

## Security Best Practices

### Development Guidelines

1. **Input Validation**
   - Always validate and sanitize user input
   - Use Pydantic models for automatic validation
   - Apply allowlisting for known-good patterns
   - Reject suspicious content patterns

2. **Authentication**
   - Use secure token generation (crypto.randomBytes)
   - Implement token rotation for long-lived services
   - Never log authentication tokens
   - Use secure headers for token transmission

3. **Error Handling**
   - Sanitize error messages to prevent information disclosure
   - Log security events separately from application logs
   - Provide generic error messages to clients
   - Include request IDs for debugging

4. **Logging**
   - Hash IP addresses for privacy compliance
   - Filter sensitive data from logs
   - Separate security logs from application logs
   - Include request tracking for audit trails

### Testing Recommendations

1. **Input Validation Testing**
   ```python
   # Test XSS prevention
   malicious_inputs = [
       '<script>alert("xss")</script>',
       'javascript:alert("xss")',
       '<img src=x onerror=alert("xss")>',
   ]
   ```

2. **Authentication Testing**
   - Test with missing tokens
   - Test with invalid tokens
   - Test token rotation scenarios
   - Test concurrent authentication attempts

3. **Rate Limiting Testing**
   - Test normal usage patterns
   - Test burst request scenarios
   - Test sustained high-rate requests
   - Test IP blocking and recovery

## Security Checklist

### Pre-deployment Security Review

#### Input Validation
- [ ] All API endpoints use Pydantic validation models
- [ ] XSS patterns are detected and blocked
- [ ] SQL injection patterns are detected and blocked
- [ ] Command injection patterns are detected and blocked
- [ ] File upload validation (if applicable)
- [ ] Request size limits enforced

#### Authentication & Authorization
- [ ] Shutdown endpoint requires valid token
- [ ] Tokens are securely generated and rotated
- [ ] No credentials logged or exposed
- [ ] Request origin validation implemented
- [ ] Proper error handling for auth failures

#### Electron Security
- [ ] Sandbox mode enabled
- [ ] Context isolation enabled
- [ ] Node integration disabled
- [ ] Web security enabled
- [ ] Secure IPC communication

#### Server Security
- [ ] Python path validation implemented
- [ ] Subprocess execution uses execFile
- [ ] Shell access disabled
- [ ] Secure environment variables
- [ ] Process isolation configured

#### Network Security
- [ ] CORS policy properly configured
- [ ] Rate limiting implemented
- [ ] Security headers added
- [ ] HTTPS enforced (production)
- [ ] Origin validation active

#### Logging & Monitoring
- [ ] Security events logged separately
- [ ] Sensitive data filtered from logs
- [ ] Request tracking implemented
- [ ] Log rotation configured
- [ ] Monitoring alerts configured

### Regular Security Maintenance Tasks

#### Weekly
- [ ] Review security logs for anomalies
- [ ] Check for failed authentication attempts
- [ ] Monitor rate limiting effectiveness
- [ ] Verify log rotation working

#### Monthly
- [ ] Update security patterns (XSS, injection, etc.)
- [ ] Review and update allowed Python paths
- [ ] Test authentication token rotation
- [ ] Review CORS configuration

#### Quarterly
- [ ] Full security audit
- [ ] Update security documentation
- [ ] Review and update threat model
- [ ] Test disaster recovery procedures

## Monitoring and Logging

### Security Logging

Dedicated security logger with separate log file:

```python
security_logger = logging.getLogger('security')
security_handler = logging.FileHandler('security.log')
security_handler.setFormatter(logging.Formatter('%(asctime)s - SECURITY - %(message)s'))
security_logger.addHandler(security_handler)
```

### Log Categories

1. **Authentication Events**
   - Successful/failed authentication attempts
   - Token rotation events
   - Unauthorized access attempts

2. **Input Validation Failures**
   - Malicious pattern detections
   - Validation errors with client IP
   - Suspicious request patterns

3. **Rate Limiting**
   - Rate limit violations
   - IP blocking events
   - Unusual traffic patterns

4. **System Security**
   - Server start/stop events
   - Configuration changes
   - Security policy violations

### Privacy Compliance

- IP addresses are hashed for logging: `hashlib.sha256(f"{ip}{salt}").hexdigest()[:16]`
- Sensitive data is filtered from logs
- Personal information is not stored in logs
- Log retention policies implemented

### Monitoring Alerts

Consider implementing alerts for:
- Multiple authentication failures
- Rate limiting violations
- Unusual request patterns
- System security events
- Log processing failures

## Threat Model

### Identified Threats and Mitigations

| Threat | Impact | Probability | Mitigation |
|--------|---------|-------------|------------|
| XSS Injection | High | Medium | Input validation, HTML escaping |
| Command Injection | Critical | Low | Path allowlisting, execFile usage |
| Rate Limiting Bypass | Medium | Medium | IP-based tracking, temporary blocking |
| Token Compromise | High | Low | Token rotation, secure generation |
| CORS Bypass | Medium | Low | Strict origin validation |
| Process Privilege Escalation | Critical | Very Low | Electron sandbox, process isolation |

### Attack Vectors

1. **Web-based Attacks**
   - XSS through text input
   - CSRF (mitigated by CORS)
   - Click-jacking (mitigated by X-Frame-Options)

2. **Network Attacks**
   - DoS via rate limiting bypass
   - Man-in-the-middle (use HTTPS in production)
   - Port scanning (mitigated by origin validation)

3. **System-level Attacks**
   - Command injection via subprocess
   - Privilege escalation via process isolation bypass
   - File system access (mitigated by path validation)

### Risk Assessment Matrix

- **Critical**: Command injection, privilege escalation
- **High**: XSS injection, token compromise
- **Medium**: Rate limiting bypass, CORS bypass
- **Low**: Information disclosure, DoS

## Version History

- **v2.1.0** (2024): Comprehensive security overhaul
  - Added Pydantic validation models
  - Implemented subprocess security
  - Enhanced authentication system
  - Added rate limiting and CORS protection
  - Enabled Electron sandbox

- **v2.0.0** (2024): Initial security implementation
  - Basic input validation
  - Simple authentication
  - CORS configuration

---

For questions about this security documentation or to report security issues, please contact the development team.

**Note**: This document should be reviewed and updated regularly as the application evolves and new security threats emerge.