# Code Style Guide

Use the existing repository style first. The rules below are defaults for common
backend, scripting, and frontend projects and should be narrowed after
initialization.

## Module Structure

MUST:

- Keep module responsibilities narrow and aligned with existing boundaries.
- Export public APIs only where callers should depend on them.
- Keep framework-specific code out of domain/core logic when the architecture
  supports layering.
- Keep generated, vendor, and dependency folders out of hand edits.

SHOULD:

- Prefer clear package boundaries over utility dumping grounds.
- Add abstractions only when they remove real duplication or stabilize a
  contract.

NEVER:

- Add hidden network calls during import, class loading, constructors, or tests.
- Cross layers for convenience when the project has an established layering
  model.

## Java / Spring Defaults

MUST:

- Keep controller, application/service, domain, and infrastructure boundaries
  explicit.
- Make transaction boundaries explicit.
- Make cache strategy, idempotency, retry, timeout, and exception handling clear.
- Follow Alibaba-style Java conventions where they do not conflict with local
  project rules.

NEVER:

- Put business logic in controllers.
- Let synchronous remote calls dominate core RT paths without justification.
- Use distributed locks as the default concurrency strategy.

## Python Defaults

MUST:

- Preserve existing typing, packaging, async/sync, and dependency conventions.
- Keep IO errors, retries, timeouts, and partial failures explicit.
- Keep scripts idempotent when they mutate files or external state.

SHOULD:

- Prefer standard library or already-used dependencies for simple tooling.
- Add tests for parsing, business rules, and edge cases.

## Frontend Defaults

MUST:

- Follow the existing framework, router, state management, component style, and
  design system.
- Cover loading, empty, error, disabled, success, and permission states.
- Keep responsive layouts stable across desktop and mobile.

NEVER:

- Replace an existing design system with one-off visual patterns for a narrow
  change.
- Ship static mock screens when the requested work is an interactive workflow.

## Error Handling

MUST:

- Preserve stable public error codes and response shapes.
- Translate exceptions at clear boundaries and preserve root causes where useful.
- Keep fallback behavior visible through logs, metrics, traces, or audit.

NEVER:

- Swallow errors silently except for best-effort observability paths.
- Convert data, permission, transaction, or downstream outages into success.

## Testing Style

MUST:

- Use the project's existing test framework and nearest useful validation.
- Use local fakes, mocks, or test doubles for external systems.
- Add focused tests near the changed path.
- Record commands and results in the feature test report.

NEVER:

- Call real payment, inventory, marketing, risk, order write, or production APIs
  from tests.
- Hide failing validation from delivery notes.
