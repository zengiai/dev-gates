# Language Code Patterns

These snippets are not universal copy-paste requirements. They define safe
default shapes until the project has narrower local patterns.

## Java Boundary Service Pattern

```java
@Service
public class OrderCommandApplicationService {

    private final OrderDomainService orderDomainService;
    private final OrderRepository orderRepository;

    public OrderCommandApplicationService(OrderDomainService orderDomainService,
                                          OrderRepository orderRepository) {
        this.orderDomainService = orderDomainService;
        this.orderRepository = orderRepository;
    }

    @Transactional(rollbackFor = Exception.class)
    public SubmitOrderResult submitOrder(SubmitOrderCommand command) {
        // 中文注释：事务边界只覆盖本地状态变更，远程通知放到事务后异步处理。
        OrderDraft draft = orderDomainService.validateAndCreateDraft(command);
        orderRepository.save(draft);
        return SubmitOrderResult.success(draft.orderNo());
    }
}
```

Use for Spring Boot application orchestration. Keep controllers thin and domain
logic out of infrastructure adapters.

## Python Immutable Decision Record

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class ExampleDecision:
    allowed: bool
    reason: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", dict(self.metadata))
```

Use for policy decisions, config snapshots, and result objects that should not
mutate after construction.

## Frontend API State Pattern

```tsx
type LoadState<T> =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: T }
  | { status: "error"; message: string };
```

Use explicit UI states so loading, empty, error, permission, and success states
cannot collapse into ambiguous booleans.

## Boundary Exception Normalization

At system boundaries:

- Preserve the root cause.
- Return a stable caller-visible error shape.
- Record logs/metrics/traces without changing the main result.
- Never convert permission, data consistency, or transaction failures into
  success.

## Focused Test Pattern

Tests should prove both caller-visible behavior and side-effect boundaries:

- invalid input does not call downstream systems;
- duplicate submissions are idempotent or rejected deterministically;
- retries are bounded;
- timeout and fallback behavior are visible;
- cache invalidation is tested when cache behavior changes.

