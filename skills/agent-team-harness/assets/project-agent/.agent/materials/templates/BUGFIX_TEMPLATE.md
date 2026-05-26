# Bug Fix Template

Use this template before changing code for a defect. The order is mandatory:
reproduce, locate, fix, validate.

## 1. Defect Summary

- Bug slug:
- Reported behavior:
- Expected behavior:
- User or caller impact:
- Severity:
- Affected version or commit:
- Affected modules:

## 2. Reproduction

- Minimal reproduction command or test:
- Input data:
- Observed output:
- Expected output:
- Is the bug deterministic: `yes` / `no`

If reproduction cannot be executed locally, document why and provide the closest
static proof.

## 3. Localization

- First failing boundary:
- Call path:
- State before failure:
- State after failure:
- Why this module owns the fix:
- Evidence:

For core-path bugs, explicitly inspect:

- QPS, latency, and error symptoms if available.
- Thread, lock, or event-loop behavior.
- DB/cache/MQ/RPC state if relevant.
- Idempotency, retry, timeout, circuit breaker, or fallback state.
- Logs, metrics, traces, and audit output.

## 4. Fix Design

- Minimal change:
- Alternatives rejected:
- Compatibility impact:
- Concurrency impact:
- Idempotency impact:
- Timeout/retry/circuit impact:
- Cache impact:
- Audit/metrics impact:
- Rollback plan:

## 5. Implementation Checklist

- Add or update a failing test first when practical.
- Keep fix scoped to the defect.
- Preserve public error codes and data contracts unless the bug is the contract.
- Avoid broad refactors in the same change.
- Do not hide permission, schema, transaction, or downstream outages with
  fallback success.

## 6. Validation

| Command | Expected | Actual | Status |
| --- | --- | --- | --- |
|  |  |  |  |

## 7. Residual Risk

- Risk:
- Why acceptable:
- Follow-up:

