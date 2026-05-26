# Change Review Checklist

Use this checklist before marking development complete and before code review.

## Scope

- [ ] The change is tied to a requirement or bug record.
- [ ] The touched modules match the approved design or bug localization.
- [ ] No unrelated refactor is included.
- [ ] Public API, error code, and data contract changes are documented.

## Stability

- [ ] Invalid inputs are rejected before downstream side effects.
- [ ] External calls have timeout behavior.
- [ ] Retry behavior is bounded or explicitly absent.
- [ ] Circuit breaker or fallback impact is documented when downstream calls are involved.
- [ ] Idempotency behavior is preserved or added for duplicate write-like calls.
- [ ] Cache TTL, invalidation, and cleanup are clear.

## Concurrency

- [ ] Shared mutable state is protected by the correct lock or isolation model.
- [ ] Multi-key locks use deterministic ordering when locks are unavoidable.
- [ ] Returned state is a snapshot or immutable value, not internal mutable data.
- [ ] No global lock serializes the whole core path without justification.

## Observability

- [ ] Metrics preserve existing names and labels or document the change.
- [ ] Logs/traces/audit include status, error code, latency, and request context where appropriate.
- [ ] Best-effort observability cannot break the main call result.

## Tests

- [ ] Focused tests cover the changed behavior.
- [ ] Negative path proves downstream was not called when preflight rejects.
- [ ] Local fakes or doubles replace external services.
- [ ] Validation command and result are recorded.

## Release Readiness

- [ ] Rollback plan is explicit.
- [ ] Residual risks are documented.
- [ ] Performance/load test need is assessed.
- [ ] Documentation or `.agent` materials were updated if the pattern changed.

