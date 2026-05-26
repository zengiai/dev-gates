# Feature Development Template

Use this template before implementing a new requirement. It complements
`.agent/templates/feature-docs/04_DEVELOPMENT.md`.

## 1. Scenario Analysis

- Feature slug:
- Caller:
- Request entry:
- Affected modules:
- Is core path affected: `yes` / `no`
- Main caller-visible behavior:

## 2. Traffic And Stability Assumptions

- Peak QPS:
- RT P99 target:
- Hot key or hotspot risk:
- Downstream capacity:
- Failure budget or acceptable degradation:
- Does this affect validation, permission, transaction, cache, MQ, RPC,
  third-party integration, audit, or metrics:

If any value is unknown, write `unknown` and explain whether implementation can
proceed safely without it.

## 3. Architecture And Boundary

- Module boundary:
- Public API change:
- Internal API change:
- Data model change:
- Compatibility impact:
- Transaction or state boundary:
- Rollback target:

## 4. Concurrency And Consistency

- Shared state:
- Locking or optimistic concurrency strategy:
- Idempotency key or fingerprint:
- Retry behavior:
- Timeout behavior:
- Circuit breaker behavior:
- Compensation or cleanup:

## 5. Cache And Runtime Protection

- Local cache:
- Remote cache:
- TTL:
- Invalidation:
- Rate-limit or isolation dimensions:
- Cleanup strategy:

## 6. Observability

- Metrics:
- Logs:
- Trace fields:
- Audit fields:
- Alert or dashboard impact:

## 7. Implementation Plan

| Step | File | Change | Risk | Test |
| --- | --- | --- | --- | --- |
| 1 |  |  |  |  |

Rules:

- Touch the smallest set of files that satisfies the approved design.
- For more than three production files, split implementation into explicit
  subtasks.
- Do not change core-path behavior without documenting why.

## 8. Validation Plan

- Focused test command:
- Full test command:
- Manual verification, if any:
- Performance or load test needed: `yes` / `no`
- Reason:

