# Cursor IDE Rules

This directory contains rules for Cursor IDE's AI assistant. These rules help maintain consistency and enforce project conventions when using AI-assisted development.

## For Contributors

These rules are **optional** for contributors. They're primarily for maintainers using Cursor IDE. If you use Cursor, you can:
- Keep these rules to follow project conventions
- Or ignore them if you prefer different AI assistance patterns

## Rules Overview

- **Security Rules**: `env_security.mdc`, `repo_security.mdc`, `security_compliance.mdc`
  - Prevent secrets from being committed
  - Enforce security best practices
  - These are critical for all contributors

- **Data Quality**: `data_quality.mdc`
  - Documents currency handling patterns (INTEGER micro-dollars)
  - Validation rules and data normalization patterns

- **API Integration**: `api_integration.mdc`
  - IBKR API client patterns
  - Error handling and retry logic

- **Testing Standards**: `testing_standards.mdc`
  - Test coverage requirements
  - Testing patterns and examples

- **Documentation**: `documentation_consistency.mdc`
  - Terminology and naming conventions
  - Documentation structure standards

## Alternative: Use CONTRIBUTING.md

For non-Cursor users, see `CONTRIBUTING.md` for:
- Code style guidelines
- Testing requirements
- Database conventions
- Security best practices
- Technology preferences

Both Cursor rules and CONTRIBUTING.md cover similar ground, but Cursor rules are more enforcement-focused for AI assistance.

