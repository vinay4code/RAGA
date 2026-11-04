# Enterprise Troubleshooting Procedures and Frequently Asked Questions
Version: v2.0
Last Updated: 2024-03-20

## 1. Authentication Troubleshooting
### Error ERR-401 Unauthorized
If you encounter error ERR-401 when attempting to authenticate, check the following:
- Verify that your corporate SSO session has not expired due to the 15-minute inactivity timeout.
- Confirm your API key in the `X-API-Key` header is active and does not contain leading or trailing whitespaces.
- Ensure your MFA security key or TOTP token is synced with the network time server.

### Error ERR-403 Forbidden
This error occurs when your user account lacks the required Role-Based Access Control (RBAC) permissions. Request the appropriate permission scope from your group administrator via the IT Service Catalog.

### Error ERR-429 Too Many Requests
When ERR-429 is received, your application has breached the standard limit of 1000 requests per hour. Implement exponential backoff in your HTTP client and parse the `Retry-After` header before submitting subsequent requests.

## 2. Network and Corporate Proxy Configuration
When connecting from behind a strict corporate firewall or proxy server, configure your HTTPS proxy environment variable:
`HTTPS_PROXY=http://proxy.corp.internal:8080`
Ensure that the internal certificate authority (CA) bundle is imported into your application's trust store.

## 3. Frequently Asked Questions (FAQ)
**Q: How often must employee passwords be changed?**
A: Passwords must be rotated every 90 days in accordance with the corporate cybersecurity baseline.

**Q: Can I use SMS authentication if my hardware security key is unavailable?**
A: SMS authentication may only be used as a temporary emergency fallback after completing phone number verification with the IT Helpdesk.
