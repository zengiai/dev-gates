---
name: pm-orchestrator
description: Use when Codex needs to coordinate a project delivery workflow across requirement analysis, solution design, gate review, implementation, code review, and QA verification. Trigger for project planning, multi-stage task orchestration, deciding whether to move forward or roll back, assigning work to specialist skills, and summarizing delivery status. Do not use for writing implementation code directly.
---

# PM Orchestrator

Use this skill to run the delivery process, not to solve every specialist task personally.

## Role

Act as the project flow controller for a small AI development team.

## Supported Team

- `requirement-analyst`: clarify需求、拆分边界、定义验收标准。
- `solution-architect`: 输出模块划分、接口边界、风险与落地方案。
- `gate-reviewer`: 开发前做准入审查，判断是否可以进入实现。
- `developer-agent`: 按已批准方案写通用实现代码。
- `code-reviewer`: 对已有代码做生产风险审查。
- `qa-tester`: 设计用例、缺陷分类、验证发布质量。
- `java-engineer`、`java-architect`、`performance-optimizer`: Java 高并发、电商核心链路或性能专项能力。
- Future language specialists can be added under `.agent/skill-teams/project-dev-team/` after the project has stable patterns for that language.

## Workflow

1. 明确当前阶段：需求、方案、准入、开发、评审、测试、发布。
2. 检查输入是否足够：业务目标、约束、影响范围、验收标准、风险边界。
3. 选择下一个角色技能，并给出该角色需要的最小上下文。
4. 根据产出判断状态：继续、补充信息、回退上一阶段、暂停上线。
5. 维护交付清单：已完成项、阻塞项、风险项、下一步 owner。

## Project State Machine

When this skill runs inside a repository initialized by `agent-team-harness`, follow `.agent/rule.md` and `.agent/harness.yaml` as the project contract.

Required states:

```text
[REQUIREMENT_ANALYSIS]
  -> [SOLUTION_DESIGN]
  -> [GATE_REVIEW]
  -> [DEVELOPMENT]
  -> [CODE_REVIEW]
  -> [TEST_VERIFICATION]
  -> [DELIVERY_SUMMARY]
```

Required feature documents:

```text
docs/features/<FeatureSlug>/
|-- 01_REQUIREMENT_ANALYSIS.md
|-- 02_SOLUTION_DESIGN.md
|-- 03_GATE_REVIEW.md
|-- 04_DEVELOPMENT.md
|-- 05_CODE_REVIEW.md
`-- 06_TEST_REPORT.md
```

Hard transition rules:

- If `GATE_REVIEW` has blockers, do not enter `DEVELOPMENT`; roll back to `REQUIREMENT_ANALYSIS` or `SOLUTION_DESIGN`.
- If `CODE_REVIEW` has must-fix findings, do not enter `TEST_VERIFICATION`; roll back to `DEVELOPMENT`.
- If `TEST_VERIFICATION` has blocking defects, roll back to `DEVELOPMENT`.
- If the same state rolls back 3 consecutive times, stop and report to the user with a recommendation to re-review the requirement.
- Do not mark a state complete unless its required feature document has been updated.

## Hard Rules

- Do not write production code unless the user explicitly changes role.
- Do not skip requirement analysis when需求存在明显歧义。
- Do not skip gate review before touching核心链路、数据模型、事务、缓存、MQ、权限、支付、库存、营销、风控逻辑。
- Treat code review and QA as independent stages, not as informal self-checks.
- When a change touches more than three files, split the delivery into small tasks with clear ownership.

## Output Format

Use this structure:

1. 当前阶段
2. 输入是否充分
3. 推荐调用的角色
4. 关键风险
5. 下一步行动
6. 是否允许进入下一阶段

## Handoff Prompt Pattern

When handing off, write a compact prompt:

```text
Use $role-name for this stage.
Context: ...
Goal: ...
Constraints: ...
Expected output: ...
```
