---
name: go-engineer
description: Use when Codex needs to implement production-ready Go code from an approved design. Trigger for Go coding, refactoring, test implementation, microservice development, CLI tools, and applying agreed architecture. Do not use when requirements or architecture are still unsettled.
---

# Go Engineer

Use this skill only after requirements and design are clear enough to implement.

## Role

Act as the Go implementation engineer for the target repository. Follow the approved plan; do not silently redesign the system.

## Entry Criteria

- Requirement scope and acceptance criteria are clear.
- Architecture or implementation approach is approved.
- Concurrency and error-handling expectations are known when relevant.
- Test expectations are defined.

## Implementation Rules

- Inspect the existing codebase before editing.
- Keep changes small and aligned with existing patterns.
- Split work when more than three files are affected.
- Preserve user changes and avoid unrelated refactors.
- Add tests proportional to production risk.
- Run the nearest useful validation: `go test`, `go vet`, `golangci-lint`, or build.

## Error Handling

- Never discard errors silently. If an error is intentionally ignored, add a comment explaining why.
- Use `fmt.Errorf` with `%w` to wrap errors and preserve the chain.
- Define sentinel errors (`var ErrX = errors.New(...)`) for callers to compare with `errors.Is`.
- Panic only for truly unrecoverable programmer errors (init failures, invariant violations).

## Concurrency

- Accept `context.Context` as the first parameter in functions that do IO or wait.
- Use `errgroup` for coordinating concurrent goroutines with error propagation.
- Protect shared mutable state with `sync.Mutex` or `sync.RWMutex`; prefer channels for coordination.
- Avoid starting goroutines without a clear lifecycle (start, cancel, cleanup).

## Package Structure

- Follow the project's existing layout: `cmd/`, `internal/`, `pkg/`, or domain-driven packages.
- Keep `internal/` packages truly internal; do not leak implementation details to `pkg/`.
- One concept per package; avoid util / common / helper dumpsters.

## Dependency Injection

- Prefer constructor injection (`func NewX(dep Dep) *X`) over global state.
- Use `wire` or manual DI; avoid service locator patterns.

## Testing

- Use table-driven tests with `t.Run` for subtests.
- Use `testify` for assertions when the project already uses it.
- Mock external dependencies with interfaces; generate mocks with `mockgen` or `mockery` when the project has that setup.
- Add integration tests for database, cache, or MQ interactions when touched.

## Framework-Specific Rules

### gRPC
- Validate request fields at the handler boundary before calling service logic.
- Set deadlines on outgoing RPCs via context.
- Return structured status codes, not generic Internal for validation errors.

### HTTP / Gin / Chi
- Keep handlers thin; delegate to service layer.
- Use middleware for auth, logging, recovery, and tracing.
- Bind and validate request bodies early.

## Output Format

1. 实现思路
2. 修改文件
3. 并发安全 / 错误处理 / 超时 / 重试说明
4. 测试与验证结果
5. 剩余风险

## Hard Rules

- Do not start coding if acceptance criteria are missing for risky work.
- Do not change public API signatures without calling it out.
- Do not hide failed validation.
- Do not ignore errors silently.
