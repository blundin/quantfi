# Security Measures (Web API, macOS-local)

Purpose: Define security posture for the local-only IBKR Client Portal Web API integration, focusing on data protection, access controls, and compliance.

## Security Posture Overview

- **Local-only operation**: No external network exposure, localhost-only access
- **No credential storage**: IBKR credentials managed by gateway, not stored by application
- **Encrypted data at rest**: SQLCipher for database, encrypted backups
- **Minimal attack surface**: Read-only API access, no trading capabilities

## Authentication & Session Security

### Gateway Authentication
- **2FA Required**: IBKR mandates two-factor authentication for all account access
- **Browser-based login**: Credentials entered only in gateway web interface
- **Session management**: Gateway handles session lifecycle, application uses local cookies
- **No credential storage**: Never store IBKR username/password in application

### Session Security
- **Cookie handling**: Treat session cookies as secrets, never log full values
- **Session expiry**: Daily reset, automatic re-authentication required
- **Localhost restriction**: Gateway only accessible from local machine
- **TLS verification**: Handle self-signed certificate appropriately in development

## Data Protection

### Encryption at Rest
- **Database encryption**: SQLCipher with strong encryption for `flex.db`
- **Backup encryption**: macOS-native encryption for backup archives
- **Key management**: Use OS keychain for encryption keys where possible
- **No plaintext storage**: All sensitive data encrypted before storage

### Data Classification
- **Sensitive**: Account IDs, position data, trade history, P&L information
- **Public**: Market data snapshots (ephemeral, not stored)
- **Logs**: Redact account identifiers, never log full API responses

### Data Retention
- **Local storage only**: All data remains on local macOS system
- **No cloud sync**: Explicitly avoid cloud storage for sensitive data
- **Backup rotation**: 30-day retention for encrypted backups
- **Cleanup procedures**: Secure deletion of old data

## Network Security

### Localhost-Only Access
- **Gateway binding**: Client Portal Gateway bound to localhost:5000 only
- **No external exposure**: No port forwarding or external access
- **Firewall considerations**: macOS firewall should block external access to port 5000
- **Network isolation**: No network sharing of sensitive data

### TLS/SSL Handling
- **Self-signed certificates**: Gateway uses self-signed certs for localhost
- **Certificate validation**: Disable strict validation for localhost in development
- **Production considerations**: Use proper certificate validation in production
- **Certificate storage**: Store trusted certificates securely

## Access Controls

### User Access
- **Single user**: Designed for single account, single user operation
- **No multi-user**: No user management or access controls needed
- **Physical security**: Rely on macOS user account security
- **Screen locking**: Encourage screen lock when unattended

### Application Access
- **Read-only API**: No trading or account modification capabilities
- **Limited scope**: Only access required data endpoints
- **No admin functions**: No account administration or settings changes
- **Audit logging**: Log all API access and data operations

## Logging & Monitoring

### Security Logging
- **Structured logs**: JSON format with consistent fields
- **Redaction**: Remove or mask sensitive information
- **Log rotation**: Regular rotation to prevent disk space issues
- **Access logging**: Log all API calls and data access

### Monitoring
- **Error patterns**: Monitor for suspicious error patterns
- **Access frequency**: Track unusual access patterns
- **Data changes**: Monitor for unexpected data modifications
- **Session activity**: Track session usage and expiry

### Log Security
- **File permissions**: Restrict log file access to application user only
- **Log integrity**: Consider log signing for tamper detection
- **Secure deletion**: Securely delete old log files
- **No external transmission**: Logs never leave local system

## Backup & Recovery Security

### Backup Encryption
- **Encrypted archives**: Use macOS-native encryption for backups
- **Key management**: Store backup encryption keys securely
- **Backup location**: Store backups in secure local location
- **Verification**: Regularly verify backup integrity

### Recovery Procedures
- **Secure restore**: Restore only to trusted systems
- **Key recovery**: Document key recovery procedures
- **Data validation**: Verify data integrity after restore
- **Access control**: Ensure restored data maintains security controls

## Compliance & Best Practices

### IBKR Compliance
- **API usage**: Follow IBKR's API usage guidelines
- **Rate limiting**: Respect API rate limits and usage policies
- **Data handling**: Comply with IBKR's data handling requirements
- **Security updates**: Stay current with IBKR security advisories

### macOS Security
- **System updates**: Keep macOS and Java updated
- **Antivirus**: Use reputable antivirus software
- **Firewall**: Enable and configure macOS firewall
- **Screen lock**: Use strong screen lock with short timeout

### Development Security
- **Code review**: Review all code for security vulnerabilities
- **Dependency management**: Keep dependencies updated
- **Secret management**: Never commit secrets to version control
- **Testing**: Include security testing in development process

## Threat Mitigation

### Common Threats
- **Phishing**: Never respond to suspicious emails claiming to be from IBKR
- **Malware**: Keep system clean with antivirus software
- **Physical access**: Secure physical access to the system
- **Data theft**: Encrypt all sensitive data at rest

### Incident Response
- **Detection**: Monitor for security incidents
- **Response**: Document response procedures
- **Recovery**: Plan for security incident recovery
- **Reporting**: Know when to report security incidents

## Security Checklist

### Initial Setup
- [ ] Enable macOS firewall
- [ ] Install and configure antivirus
- [ ] Set up screen lock with short timeout
- [ ] Configure secure backup location
- [ ] Test backup and restore procedures

### Ongoing Security
- [ ] Regular security updates
- [ ] Monitor log files for anomalies
- [ ] Verify backup integrity
- [ ] Review access patterns
- [ ] Update security documentation

### Before Deployment
- [ ] Security code review
- [ ] Penetration testing
- [ ] Backup verification
- [ ] Incident response plan
- [ ] Security training

## References
- IBKR Security: https://www.interactivebrokers.com/en/general/security-your-account.php
- IBKR Security Best Practices: https://www.interactivebrokers.com/en/general/security-best-practices.php
- Web API overview: `docs/ib_web_api.md`
- Authentication guide: `docs/ib_web_api_auth.md`
- Error handling: `docs/error_handling_retry.md`
