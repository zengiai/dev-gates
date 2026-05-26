# Project Agent Team Rules

## 1. Harness Definition

This repository uses a project-local AI development harness under `.agent/`.
The harness defines workflow gates, role boundaries, model routing, code
materials, feature documents, and executable checks for non-trivial development.

The priority order is fixed:

1. Stability first.
2. Performance second.
3. Extensibility third.
4. Elegance last.

Agents MUST protect the main business or runtime path before optimizing
abstraction, style, or reuse.

## 2. Team Skill Integration

The pinned team skills live in:

```text
.agent/skill-teams/project-dev-team/
```

Agents MUST NOT silently sync global skill changes into this project. Any role
addition, role deletion, or skill update is a project change and requires review.

Language coverage is intentionally extensible. If the project needs a role that
does not exist yet, use `developer-agent` plus the project materials, then add a
specialist role only after the pattern is stable.

## 3. Model Routing

Model routing is project-specific and stored in `.agent/harness.yaml` plus
`.agent/generated/model-routing.md`.

MUST:

- Inspect available models for the current project before finalizing routing.
- Use the strongest suitable model for implementation roles and code review.
- Use a strong reasoning model for architecture and performance risk work.
- Use a balanced model for PM, requirement analysis, gate review, and QA unless
  the change is core-path or high-risk.
- Record any escalation reason in the feature document.

SHOULD:

- Prefer reliability and tool support over benchmark-only ranking.
- Re-run initialization when a project moves to a different model family.

NEVER:

- Copy another project's fixed model names without checking availability.
- Run implementation through planning or QA roles to bypass the routing policy.

## 4. Workflow State Machine

PM Orchestrator controls the state machine. Every non-trivial requirement MUST
move through:

```text
[REQUIREMENT_ANALYSIS]
  -> [SOLUTION_DESIGN]
  -> [GATE_REVIEW]
  -> [DEVELOPMENT]
  -> [CODE_REVIEW]
  -> [TEST_VERIFICATION]
  -> [DELIVERY_SUMMARY]
```

Hard rules:

- If `GATE_REVIEW` has blockers, development MUST NOT start.
- If `CODE_REVIEW` has must-fix findings, testing MUST NOT start.
- If `TEST_VERIFICATION` has blocking defects, roll back to `DEVELOPMENT`.
- If the same state rolls back 3 consecutive times, stop and ask for
  requirement or architecture re-review.
- A state MUST NOT be marked complete without updating its required document.

Script gates are mandatory:

```bash
python .agent/scripts/workflow_guard.py check-materials
python .agent/scripts/workflow_guard.py init <FeatureSlug>
python .agent/scripts/workflow_guard.py init <BugSlug> --kind bugfix
python .agent/scripts/workflow_guard.py enter <FeatureSlug> DEVELOPMENT
python .agent/scripts/workflow_guard.py pre-edit <FeatureSlug> --files <paths>
python .agent/scripts/workflow_guard.py complete <FeatureSlug> DEVELOPMENT
python .agent/scripts/workflow_guard.py enter <FeatureSlug> TEST_VERIFICATION
python .agent/scripts/workflow_guard.py complete <FeatureSlug> TEST_VERIFICATION
```

NEVER:

- Proceed past a script gate with `BLOCKED`.
- Replace a script gate with a prose claim.
- Ignore the pre-edit split warning when planned production edits exceed 3 files.
- Modify code for a bug when `00_BUGFIX.md` lacks reproduction, localization,
  fix design, or validation content.

## 5. Mandatory Feature Documents

Every non-trivial requirement MUST have:

```text
docs/features/<FeatureSlug>/
|-- 01_REQUIREMENT_ANALYSIS.md
|-- 02_SOLUTION_DESIGN.md
|-- 03_GATE_REVIEW.md
|-- 04_DEVELOPMENT.md
|-- 05_CODE_REVIEW.md
`-- 06_TEST_REPORT.md
```

MUST:

- Use a stable English `FeatureSlug`, for example `SchedulePostUpdateBehavior`.
- Keep each document as durable output of its state, not a chat transcript.
- Include assumptions, decisions, risks, rollback conditions, and validation
  evidence.

NEVER:

- Treat chat messages as the only requirement record.
- Start implementation when `03_GATE_REVIEW.md` is missing or not approved.
- Start test verification when `05_CODE_REVIEW.md` has unresolved must-fix items.

## 6. Role Boundaries

| Role | Owns | MUST NOT |
| --- | --- | --- |
| `pm-orchestrator` | State machine, owner routing, blocker tracking | Write production code |
| `requirement-analyst` | Scope, non-scope, acceptance criteria, ambiguity | Decide implementation details |
| `solution-architect` | Modules, interfaces, consistency, rollout, risks | Skip gate review for risky work |
| `gate-reviewer` | Go/no-go readiness decision | Approve missing rollback or observability |
| `developer-agent` | General implementation across supported languages | Redesign architecture silently |
| `java-architect` | Java high-concurrency and e-commerce architecture | Replace small-change engineering judgment |
| `java-engineer` | Spring Boot / Java implementation | Start before architecture is approved |
| `performance-optimizer` | QPS, RT, hotspot, cache, capacity analysis | Replace requirement analysis |
| `code-reviewer` | Production risk review | Convert review into broad refactoring |
| `qa-tester` | Test plan, regression, defect classification | Replace code review |

## 7. File Boundaries

Agents MAY write paths listed in `.agent/harness.yaml` under
`write_boundaries.allowed`.

Agents MUST NOT modify unless explicitly requested:

- `.git/**`
- IDE metadata
- local secrets, credentials, or environment files
- generated dependency folders
- unrelated documentation sections

## 8. Execution Boundaries

MUST:

- Inspect relevant code before editing.
- Keep changes scoped to the current feature or fix.
- Run the nearest useful validation after code changes.
- Report failed or skipped validation explicitly.
- Preserve user changes in the working tree.

NEVER:

- Connect to or mutate production systems.
- Call real payment, inventory, marketing, risk-control, or order write APIs from
  tests or local verification.
- Run destructive Git commands unless explicitly requested.
- Introduce hidden remote dependencies or background services.

## 9. Core Path Rules

Core paths are generated into:

```text
.agent/generated/core_paths.txt
```

Before changing core paths, Agents MUST state:

- Request entry and call path.
- State or transaction boundary.
- Idempotency strategy.
- Timeout, retry, circuit breaker, and degradation behavior.
- Audit and metrics compatibility.
- Rollback plan.

NEVER:

- Let a distributed lock, single database row, or synchronous remote call become
  the core bottleneck without explicit justification.
- Hide policy denial, circuit breaking, idempotency hits, or approval waits from
  logs, metrics, or audit where applicable.

## 10. Stability Rules

MUST:

- Add timeouts to external calls.
- Bound retries and prevent retry amplification.
- Keep high-risk operations approvable, auditable, and traceable.
- Use clear rate-limit or isolation dimensions when traffic protection exists.
- Preserve compatibility unless a breaking change is approved.

SHOULD:

- Evaluate QPS, RT P99, error rate, rejection rate, cache hit rate, queue depth,
  and downstream backlog for core-path changes.
- Prefer optimistic concurrency, batching, async buffering, and cache isolation
  over global locks.

NEVER:

- Treat manual production handling as a valid fallback for predictable failure
  paths.
- Approve a core-path change without rollback and observability.

## 11. Testing Rules

Default validation is defined in `.agent/harness.yaml`.

MUST:

- Add or update tests proportional to production risk.
- Include executed commands and results in `06_TEST_REPORT.md`.
- State untested areas and residual risks.

NEVER:

- Mark testing complete if blocker defects remain.
- Hide failing validation from the final delivery summary.

## 12. Output Contracts

System design output MUST include:

1. Scenario analysis.
2. Traffic model assumptions.
3. Architecture design.
4. Data model design.
5. Concurrency control.
6. Bottleneck prediction.
7. Risks and fallback.
8. Monitoring and alerting.
9. Evolution path.

Code delivery output MUST include:

1. Implementation approach.
2. Modified files.
3. Thread-safety, transaction, cache, and exception handling notes.
4. Test and validation results.
5. Residual risks.

Incident or bug-fix output MUST include:

1. Diagnosis path.
2. Reproduction method.
3. Fix strategy.
4. Whether load testing is required.

## 13. Code Materials

Agents MUST use these materials before changing production code:

- `.agent/materials/project-code-profile.md`
- `.agent/materials/code-style-guide.md`
- `.agent/materials/templates/FEATURE_DEVELOPMENT_TEMPLATE.md`
- `.agent/materials/templates/BUGFIX_TEMPLATE.md`
- `.agent/materials/templates/LANGUAGE_CODE_PATTERNS.md`
- `.agent/materials/checklists/CHANGE_REVIEW_CHECKLIST.md`

Feature development MUST follow the feature development template and update
`04_DEVELOPMENT.md`.

Bug fixes MUST follow the bug-fix template in this order:

1. Reproduce.
2. Locate.
3. Fix.
4. Validate.

## 14. Continuous Improvement

After a large feature reaches `DELIVERY_SUMMARY`, run:

```bash
python .agent/scripts/feature_improvement.py <FeatureSlug>
```

MUST:

- Summarize reusable lessons from the feature documents.
- Update `.agent/materials`, templates, role skills, or rules only when the lesson
  is repeatable and not project noise.
- Keep improvement changes small and reviewable.

NEVER:

- Rewrite team rules based on a one-off workaround without calling out the risk.
- Hide unresolved feature defects as process improvements.

