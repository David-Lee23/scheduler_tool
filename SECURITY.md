# Security Guidelines

## Data Protection

This application handles sensitive trucking schedule data. Follow these guidelines to ensure data security:

### What's Protected by .gitignore

- ✅ PDF files (`*.pdf`)
- ✅ Database files (`*.db`, `*.sqlite`, `*.sqlite3`)
- ✅ CSV files (`*.csv`)
- ✅ Upload directories (`uploads/`, `pdfs/`)
- ✅ Configuration files with sensitive data (`config.json`)
- ✅ Log files (`*.log`)

### Before Making Repository Public

**CRITICAL STEPS:**

1. ✅ Verify `.gitignore` includes all data file types
2. ✅ Remove any committed data files: `git rm --cached *.db *.pdf`
3. ✅ Check git history for sensitive data: `git log --name-only`
4. ✅ Consider using BFG Repo-Cleaner for thorough cleanup if needed
5. ✅ Test with fresh clone to ensure no data is exposed

### Ongoing Security Practices

- 🔐 Never commit actual company data
- 🔐 Use environment variables for sensitive configuration
- 🔐 Regularly backup your local database (outside of git)
- 🔐 Implement access controls in production deployments
- 🔐 Monitor for accidental data commits

### Local Development

- Data files stay on your local machine only
- Database is created automatically on first PDF upload
- All uploaded files remain in local directories only
- No company data is ever transmitted to version control

### Production Deployment

If deploying this system:

- Use a separate, secure server
- Implement proper authentication
- Use HTTPS/TLS encryption
- Regular security updates
- Data backup procedures
- Access logging and monitoring

## Reporting Security Issues

If you find security vulnerabilities, please report them responsibly by:

1. **DO NOT** create public GitHub issues
2. Contact the maintainers directly
3. Provide detailed information about the vulnerability
4. Allow time for fix before public disclosure 