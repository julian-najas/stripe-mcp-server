# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

**Please DO NOT open a public issue for security vulnerabilities.**

Instead, report security issues privately:

1. **Email**: Send details to the repository maintainer (check GitHub profile)
2. **GitHub Security Advisories**: Use the "Security" tab → "Report a vulnerability"

### What to Include

Please provide:

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)
- Your contact information

### Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial assessment**: Within 1 week
- **Fix timeline**: Depends on severity (critical: days, low: weeks)

### Security Best Practices

When using this project:

1. **Never commit secrets**
   - Use `.env` for local secrets (already in `.gitignore`)
   - Use environment variables in production

2. **Stripe keys**
   - Use test keys (`sk_test_`) for development
   - Never expose `sk_live_` keys in code/logs
   - Rotate keys if exposed

3. **Webhook secrets**
   - Always verify Stripe webhook signatures
   - Use unique `whsec_` per environment
   - Don't reuse webhook secrets

4. **API authentication**
   - Change default `API_KEY` in production
   - Use strong, random keys (32+ characters)
   - Implement rate limiting in production

5. **Database**
   - Use PostgreSQL in production (not SQLite)
   - Enable SSL for database connections
   - Regular backups

6. **Dependencies**
   - Regularly update dependencies: `pip install --upgrade -e ".[dev]"`
   - Monitor security advisories

### Known Security Considerations

- **Idempotency keys**: 24-hour TTL by default (configurable)
- **Webhook replay**: Handled via signature verification
- **Rate limiting**: Not implemented (add in production)
- **HTTPS**: Required in production for webhook endpoints

## Security Updates

Security patches will be released as minor/patch versions and announced in:
- GitHub Security Advisories
- Release notes
- README (if critical)

## Hall of Fame

Security researchers who responsibly disclose vulnerabilities will be acknowledged here (with permission).

---

Thank you for helping keep this project secure! 🔒
