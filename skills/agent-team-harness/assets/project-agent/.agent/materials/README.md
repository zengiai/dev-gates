# Project Code Materials

These materials are mandatory for future feature development and bug fixes in
this repository. They are generated during initialization, then maintained by the
project team as reusable engineering knowledge.

## Required Reading Order

For feature development:

1. `.agent/rule.md`
2. `.agent/materials/project-code-profile.md`
3. `.agent/materials/code-style-guide.md`
4. `.agent/materials/templates/FEATURE_DEVELOPMENT_TEMPLATE.md`
5. `.agent/materials/templates/LANGUAGE_CODE_PATTERNS.md`
6. `.agent/materials/checklists/CHANGE_REVIEW_CHECKLIST.md`

For bug fixes:

1. `.agent/rule.md`
2. `.agent/materials/project-code-profile.md`
3. `.agent/materials/templates/BUGFIX_TEMPLATE.md`
4. `.agent/materials/code-style-guide.md`
5. `.agent/materials/checklists/CHANGE_REVIEW_CHECKLIST.md`

## Mandatory Output Before Code Changes

Before modifying production code, the agent MUST state:

- Affected request entry and call path.
- State, transaction, and idempotency boundary.
- Timeout, retry, circuit breaker, and degradation impact.
- Cache and concurrency impact.
- Audit, metrics, and trace impact.
- Focused validation command.

Small documentation-only updates may skip code-path analysis, but must say why.

