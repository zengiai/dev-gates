#!/usr/bin/env python3
"""Scripted guardrails for the project agent workflow.

The guard intentionally uses only Python's standard library. It turns the most
important `.agent` MUST rules into executable checks so agents cannot rely on
memory or prose-only compliance.
"""

from __future__ import annotations

import argparse
import fnmatch
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Sequence


REPO_ROOT = Path(__file__).resolve().parents[2]
AGENT_ROOT = REPO_ROOT / ".agent"
TEMPLATE_ROOT = AGENT_ROOT / "templates" / "feature-docs"
FEATURE_ROOT = REPO_ROOT / "docs" / "features"
GENERATED_ROOT = AGENT_ROOT / "generated"

STAGE_DOCS: dict[str, str] = {
    "REQUIREMENT_ANALYSIS": "01_REQUIREMENT_ANALYSIS.md",
    "SOLUTION_DESIGN": "02_SOLUTION_DESIGN.md",
    "GATE_REVIEW": "03_GATE_REVIEW.md",
    "DEVELOPMENT": "04_DEVELOPMENT.md",
    "CODE_REVIEW": "05_CODE_REVIEW.md",
    "TEST_VERIFICATION": "06_TEST_REPORT.md",
    "DELIVERY_SUMMARY": "06_TEST_REPORT.md",
}

STAGE_ORDER: tuple[str, ...] = (
    "REQUIREMENT_ANALYSIS",
    "SOLUTION_DESIGN",
    "GATE_REVIEW",
    "DEVELOPMENT",
    "CODE_REVIEW",
    "TEST_VERIFICATION",
    "DELIVERY_SUMMARY",
)

REQUIRED_DOCS: tuple[str, ...] = (
    "01_REQUIREMENT_ANALYSIS.md",
    "02_SOLUTION_DESIGN.md",
    "03_GATE_REVIEW.md",
    "04_DEVELOPMENT.md",
    "05_CODE_REVIEW.md",
    "06_TEST_REPORT.md",
)

BUGFIX_DOC = "00_BUGFIX.md"
BUGFIX_TEMPLATE = AGENT_ROOT / "materials" / "templates" / "BUGFIX_TEMPLATE.md"

MATERIALS: tuple[str, ...] = (
    ".agent/materials/project-code-profile.md",
    ".agent/materials/code-style-guide.md",
    ".agent/materials/templates/FEATURE_DEVELOPMENT_TEMPLATE.md",
    ".agent/materials/templates/BUGFIX_TEMPLATE.md",
    ".agent/materials/templates/LANGUAGE_CODE_PATTERNS.md",
    ".agent/materials/checklists/CHANGE_REVIEW_CHECKLIST.md",
)

DEFAULT_PRODUCTION_PATH_PATTERNS: tuple[str, ...] = (
    "src/**",
    "app/**",
    "lib/**",
    "packages/**/src/**",
    "services/**",
    "internal/**",
    "cmd/**",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "pyproject.toml",
    "package.json",
    "go.mod",
    "Cargo.toml",
)

DEFAULT_CORE_PATH_PATTERNS: tuple[str, ...] = (
    "src/**/order/**",
    "src/**/payment/**",
    "src/**/inventory/**",
    "src/**/risk/**",
    "src/**/security/**",
    "src/**/auth/**",
    "src/**/gateway/**",
    "src/**/transaction/**",
    "src/**/cache/**",
    "src/**/mq/**",
)

YES_VALUES = {"yes", "y", "true", "done", "ok", "是", "已完成"}
NONE_VALUES = {"none", "n/a", "na", "no", "无", "none."}

INSTRUCTIONAL_PHRASES: tuple[str, ...] = (
    "Describe the",
    "Describe a",
    "Describe the smallest",
    "If any value is unknown",
)


@dataclass(frozen=True)
class GuardResult:
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return not self.errors


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Executable workflow guard for .agent MUST rules.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="create feature documents from templates")
    init_parser.add_argument("slug", help="StableEnglishPascalCase feature slug")
    init_parser.add_argument(
        "--kind",
        choices=("feature", "bugfix"),
        default="feature",
        help="workflow kind; bugfix creates an additional 00_BUGFIX.md gate document",
    )

    status_parser = subparsers.add_parser("status", help="show workflow document status")
    status_parser.add_argument("slug", help="feature slug")

    enter_parser = subparsers.add_parser("enter", help="check whether a stage may start")
    enter_parser.add_argument("slug", help="feature slug")
    enter_parser.add_argument("stage", choices=STAGE_ORDER, help="target workflow stage")

    complete_parser = subparsers.add_parser("complete", help="check whether a stage may finish")
    complete_parser.add_argument("slug", help="feature slug")
    complete_parser.add_argument("stage", choices=STAGE_ORDER, help="workflow stage")

    pre_edit_parser = subparsers.add_parser("pre-edit", help="check before editing production code")
    pre_edit_parser.add_argument("slug", help="feature slug")
    pre_edit_parser.add_argument("--files", nargs="+", required=True, help="files planned for editing")

    subparsers.add_parser("check-materials", help="verify mandatory .agent materials exist")
    subparsers.add_parser("generate-hooks", help="generate git pre-commit hook and CI guard configuration")

    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            result = init_feature(args.slug, kind=args.kind)
        elif args.command == "status":
            result = status(args.slug)
        elif args.command == "enter":
            result = enter_stage(args.slug, args.stage)
        elif args.command == "complete":
            result = complete_stage(args.slug, args.stage)
        elif args.command == "pre-edit":
            result = pre_edit(args.slug, args.files)
        elif args.command == "check-materials":
            result = check_materials()
        elif args.command == "generate-hooks":
            result = generate_hooks()
        else:  # pragma: no cover - argparse prevents this branch.
            raise ValueError(f"unsupported command: {args.command}")
    except GuardUsageError as exc:
        result = GuardResult(errors=(str(exc),))

    print_result(result)
    return 0 if result.ok else 1


class GuardUsageError(ValueError):
    """Raised when the guard command input is invalid."""


def init_feature(slug: str, *, kind: str = "feature") -> GuardResult:
    _validate_slug(slug)
    errors = list(check_materials().errors)
    if errors:
        return GuardResult(errors=tuple(errors))

    feature_dir = _feature_dir(slug)
    feature_dir.mkdir(parents=True, exist_ok=True)
    created: list[str] = []
    kept: list[str] = []
    for doc_name in REQUIRED_DOCS:
        source = TEMPLATE_ROOT / doc_name
        target = feature_dir / doc_name
        if target.exists():
            kept.append(_display_path(target))
            continue
        text = source.read_text(encoding="utf-8")
        text = _fill_initial_template_values(text, slug)
        target.write_text(text, encoding="utf-8")
        created.append(_display_path(target))

    if kind == "bugfix":
        bugfix_target = feature_dir / BUGFIX_DOC
        if bugfix_target.exists():
            kept.append(_display_path(bugfix_target))
        else:
            text = BUGFIX_TEMPLATE.read_text(encoding="utf-8")
            text = text.replace("- Bug slug:", f"- Bug slug: {slug}")
            bugfix_target.write_text(text, encoding="utf-8")
            created.append(_display_path(bugfix_target))

    notes = [f"feature folder: {_display_path(feature_dir)}"]
    notes.extend(f"created: {item}" for item in created)
    notes.extend(f"kept existing: {item}" for item in kept)
    notes.append(f"next: python .agent/scripts/workflow_guard.py enter {slug} REQUIREMENT_ANALYSIS")
    return GuardResult(notes=tuple(notes))


def status(slug: str) -> GuardResult:
    _validate_slug(slug)
    feature_dir = _feature_dir(slug)
    if not feature_dir.exists():
        return GuardResult(
            errors=(f"feature folder does not exist: {_display_path(feature_dir)}",),
            notes=(f"run: python .agent/scripts/workflow_guard.py init {slug}",),
        )

    notes: list[str] = [f"feature folder: {_display_path(feature_dir)}"]
    warnings: list[str] = []
    for stage, doc_name in STAGE_DOCS.items():
        doc_path = feature_dir / doc_name
        if not doc_path.exists():
            notes.append(f"{stage}: missing {doc_name}")
            continue
        text = doc_path.read_text(encoding="utf-8")
        if _doc_has_unresolved_placeholders(text):
            notes.append(f"{stage}: needs update {doc_name}")
        else:
            notes.append(f"{stage}: updated {doc_name}")
    material_result = check_materials()
    warnings.extend(material_result.errors)
    return GuardResult(warnings=tuple(warnings), notes=tuple(notes))


def enter_stage(slug: str, stage: str) -> GuardResult:
    _validate_slug(slug)
    _validate_stage(stage)
    feature_dir = _require_feature_dir(slug)
    errors = list(check_materials().errors)

    for previous_stage in _previous_stages(stage):
        errors.extend(_assert_stage_complete(feature_dir, previous_stage))

    notes = (
        f"enter {stage}: {'allowed' if not errors else 'blocked'}",
        f"stage document: {_display_path(feature_dir / STAGE_DOCS[stage])}",
    )
    return GuardResult(errors=tuple(errors), notes=notes)


def complete_stage(slug: str, stage: str) -> GuardResult:
    _validate_slug(slug)
    _validate_stage(stage)
    feature_dir = _require_feature_dir(slug)
    errors = list(check_materials().errors)
    errors.extend(_assert_doc_complete(feature_dir / STAGE_DOCS[stage]))

    if stage == "GATE_REVIEW":
        errors.extend(_assert_gate_allows_development(feature_dir))
    elif stage == "DEVELOPMENT":
        errors.extend(_assert_development_material_compliance(feature_dir))
    elif stage == "CODE_REVIEW":
        errors.extend(_assert_code_review_allows_testing(feature_dir))
    elif stage in {"TEST_VERIFICATION", "DELIVERY_SUMMARY"}:
        errors.extend(_assert_test_report_ready(feature_dir))

    notes = (
        f"complete {stage}: {'allowed' if not errors else 'blocked'}",
        f"stage document: {_display_path(feature_dir / STAGE_DOCS[stage])}",
    )
    return GuardResult(errors=tuple(errors), notes=notes)


def pre_edit(slug: str, files: Sequence[str]) -> GuardResult:
    _validate_slug(slug)
    if not files:
        raise GuardUsageError("--files must contain at least one path")

    normalized_files = tuple(_normalize_repo_path(item) for item in files)
    errors = list(enter_stage(slug, "DEVELOPMENT").errors)

    production_files = tuple(item for item in normalized_files if _is_production_path(item))
    if len(production_files) > 3:
        errors.append(
            "planned production edits exceed 3 files; split the task before editing: "
            + ", ".join(production_files)
        )

    core_files = tuple(item for item in normalized_files if _is_core_path(item))
    if core_files:
        feature_dir = _require_feature_dir(slug)
        errors.extend(_assert_core_path_change_notes(feature_dir))

    bugfix_doc = _require_feature_dir(slug) / BUGFIX_DOC
    if bugfix_doc.exists():
        errors.extend(_assert_bugfix_ready(bugfix_doc))

    notes = [
        f"pre-edit: {'allowed' if not errors else 'blocked'}",
        "planned files:",
        *[f"- {item}" for item in normalized_files],
    ]
    if core_files:
        notes.append("core-path files detected:")
        notes.extend(f"- {item}" for item in core_files)
    return GuardResult(errors=tuple(errors), notes=tuple(notes))


def check_materials() -> GuardResult:
    missing = [
        f"missing mandatory material: {item}"
        for item in MATERIALS
        if not (REPO_ROOT / item).exists()
    ]
    if not TEMPLATE_ROOT.exists():
        missing.append(f"missing template root: {_display_path(TEMPLATE_ROOT)}")
    if not BUGFIX_TEMPLATE.exists():
        missing.append(f"missing bugfix template: {_display_path(BUGFIX_TEMPLATE)}")
    for doc_name in REQUIRED_DOCS:
        path = TEMPLATE_ROOT / doc_name
        if not path.exists():
            missing.append(f"missing feature template: {_display_path(path)}")
    return GuardResult(errors=tuple(missing), notes=("materials ok",) if not missing else ())


def generate_hooks() -> GuardResult:
    """Generate git pre-commit hook and GitHub Actions CI guard configuration.

    Installs files into:
      - .git/hooks/pre-commit  (shell hook that runs workflow_guard.py pre-edit)
      - .github/workflows/agent-guard.yml  (optional CI guard)
    Existing hooks are not overwritten; notes are emitted instead.
    """
    notes: list[str] = []
    errors: list[str] = []

    # ── pre-commit hook ──
    hook_dir = REPO_ROOT / ".git" / "hooks"
    hook_path = hook_dir / "pre-commit"
    if hook_dir.exists():
        if hook_path.exists():
            notes.append(
                f"pre-commit hook already exists at {_display_path(hook_path)}; "
                "merge the guard snippet manually from .agent/generated/pre-commit-hook.sh"
            )
        else:
            hook_content = _pre_commit_hook_script()
            hook_path.write_text(hook_content, encoding="utf-8")
            _make_executable(hook_path)
            notes.append(f"installed pre-commit hook: {_display_path(hook_path)}")
    else:
        notes.append(".git directory not found; skipping pre-commit hook installation")

    # Also write a standalone copy under .agent/generated for manual review
    generated_hook = GENERATED_ROOT / "pre-commit-hook.sh"
    generated_hook.parent.mkdir(parents=True, exist_ok=True)
    generated_hook.write_text(_pre_commit_hook_script(), encoding="utf-8")
    notes.append(f"standalone hook script: {_display_path(generated_hook)}")

    # ── CI guard workflow ──
    ci_dir = REPO_ROOT / ".github" / "workflows"
    ci_path = ci_dir / "agent-guard.yml"
    ci_dir.mkdir(parents=True, exist_ok=True)
    if ci_path.exists():
        notes.append(f"CI guard workflow already exists: {_display_path(ci_path)}; skipping")
    else:
        ci_path.write_text(_ci_guard_workflow(), encoding="utf-8")
        notes.append(f"installed CI guard: {_display_path(ci_path)}")

    return GuardResult(errors=tuple(errors), notes=tuple(notes))


def _pre_commit_hook_script() -> str:
    return """#!/bin/sh
# Generated by workflow_guard.py generate-hooks — review before use.
# Runs workflow guard pre-edit on staged production files.

GUARD="python .agent/scripts/workflow_guard.py"

# Detect the current feature slug from the active feature directory
FEATURE_DIR="docs/features"
SLUG=""
if [ -d "$FEATURE_DIR" ]; then
    # Pick the most recently modified feature folder as the active feature
    SLUG=$(ls -1t "$FEATURE_DIR" 2>/dev/null | head -1)
fi

if [ -z "$SLUG" ]; then
    echo "[agent-guard] No active feature found. Skipping pre-commit guard."
    exit 0
fi

# Collect staged files that are inside production paths
STAGED=$(git diff --cached --name-only --diff-filter=ACM)
if [ -z "$STAGED" ]; then
    exit 0
fi

echo "[agent-guard] Running pre-edit check for feature: $SLUG"
set -- $STAGED
$GUARD pre-edit "$SLUG" --files "$@"
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "[agent-guard] BLOCKED: pre-edit guard failed."
    echo "Resolve the errors above before committing."
    exit 1
fi

echo "[agent-guard] PASS"
"""


def _ci_guard_workflow() -> str:
    return """name: agent-guard
on: [pull_request]
jobs:
  guard:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Check materials
        run: python .agent/scripts/workflow_guard.py check-materials
"""


def _assert_stage_complete(feature_dir: Path, stage: str) -> list[str]:
    errors = _assert_doc_complete(feature_dir / STAGE_DOCS[stage])
    if stage == "GATE_REVIEW":
        errors.extend(_assert_gate_allows_development(feature_dir))
    elif stage == "DEVELOPMENT":
        errors.extend(_assert_development_material_compliance(feature_dir))
    elif stage == "CODE_REVIEW":
        errors.extend(_assert_code_review_allows_testing(feature_dir))
    elif stage in {"TEST_VERIFICATION", "DELIVERY_SUMMARY"}:
        errors.extend(_assert_test_report_ready(feature_dir))
    return errors


def _assert_doc_complete(path: Path) -> list[str]:
    if not path.exists():
        return [f"required document is missing: {_display_path(path)}"]
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    if _doc_has_unresolved_placeholders(text):
        errors.append(f"document still contains placeholders: {_display_path(path)}")
    for phrase in INSTRUCTIONAL_PHRASES:
        if phrase in text:
            errors.append(f"document still contains template instruction {phrase!r}: {_display_path(path)}")
            break
    return errors


def _assert_gate_allows_development(feature_dir: Path) -> list[str]:
    path = feature_dir / "03_GATE_REVIEW.md"
    text = _read_required(path)
    errors: list[str] = []
    decision = _field_value(text, "Decision")
    if decision not in {"GO", "CONDITIONAL GO"}:
        errors.append("gate review decision must be GO or CONDITIONAL GO before development")
    blocker_rows = _table_rows_in_section(text, "Blockers")
    real_blockers = [row for row in blocker_rows if not _row_is_none(row)]
    if real_blockers:
        errors.append("gate review has unresolved blockers; development must not start")
    return errors


def _assert_development_material_compliance(feature_dir: Path) -> list[str]:
    text = _read_required(feature_dir / "04_DEVELOPMENT.md")
    labels = (
        "Project profile read",
        "Style guide read",
        "Feature template applied",
        "Language code patterns applied",
        "Review checklist applied before handoff",
    )
    errors = []
    for label in labels:
        if not _field_is_yes(text, label):
            errors.append(f"development material compliance missing yes: {label}")
    return errors


def _assert_core_path_change_notes(feature_dir: Path) -> list[str]:
    path = feature_dir / "04_DEVELOPMENT.md"
    text = _read_required(path)
    required_sections = (
        "Transaction / State Boundary",
        "Thread Safety",
        "Cache Strategy",
        "Idempotency Strategy",
        "Timeout / Retry / Circuit Breaker / Degradation",
        "Exception Handling",
        "Audit And Observability",
    )
    errors = []
    for section in required_sections:
        body = _section_text(text, section)
        if not body or _doc_has_unresolved_placeholders(body):
            errors.append(f"core-path pre-edit notes are incomplete: {section}")
    return errors


def _assert_bugfix_ready(path: Path) -> list[str]:
    errors = _assert_doc_complete(path)
    text = _read_required(path)
    required_sections = (
        "Defect Summary",
        "Reproduction",
        "Localization",
        "Fix Design",
        "Validation",
    )
    for section in required_sections:
        body = _section_text(text, section)
        if not body or _doc_has_unresolved_placeholders(body):
            errors.append(f"bugfix gate section is incomplete: {section}")
    return errors


def _assert_code_review_allows_testing(feature_dir: Path) -> list[str]:
    text = _read_required(feature_dir / "05_CODE_REVIEW.md")
    errors: list[str] = []
    decision = _field_value(text, "Decision")
    if decision not in {"APPROVED", "APPROVED_WITH_NOTES"}:
        errors.append("code review decision must be APPROVED or APPROVED_WITH_NOTES before testing")
    must_fix = _section_text(text, "Must-Fix Items Before Test Verification")
    if must_fix and not _content_is_none(must_fix):
        errors.append("code review has unresolved must-fix items; testing must not start")
    return errors


def _assert_test_report_ready(feature_dir: Path) -> list[str]:
    text = _read_required(feature_dir / "06_TEST_REPORT.md")
    errors: list[str] = []
    decision = _field_value(text, "Decision")
    if decision != "READY":
        errors.append("test report release readiness decision must be READY")
    if not _field_is_yes(text, "Rollback plan verified"):
        errors.append("rollback plan must be verified before delivery")
    if not _field_is_yes(text, "Observability verified"):
        errors.append("observability must be verified before delivery")
    return errors


def _previous_stages(stage: str) -> tuple[str, ...]:
    index = STAGE_ORDER.index(stage)
    return STAGE_ORDER[:index]


def _validate_stage(stage: str) -> None:
    if stage not in STAGE_DOCS:
        raise GuardUsageError(f"unknown stage: {stage}")


def _validate_slug(slug: str) -> None:
    if not re.fullmatch(r"[A-Z][A-Za-z0-9]*", slug):
        raise GuardUsageError(
            "slug must use StableEnglishPascalCase, for example SchedulePostUpdateBehavior"
        )


def _feature_dir(slug: str) -> Path:
    return FEATURE_ROOT / slug


def _require_feature_dir(slug: str) -> Path:
    feature_dir = _feature_dir(slug)
    if not feature_dir.exists():
        raise GuardUsageError(
            f"feature folder does not exist: {_display_path(feature_dir)}; "
            f"run: python .agent/scripts/workflow_guard.py init {slug}"
        )
    return feature_dir


def _read_required(path: Path) -> str:
    if not path.exists():
        raise GuardUsageError(f"required document is missing: {_display_path(path)}")
    return path.read_text(encoding="utf-8")


def _fill_initial_template_values(text: str, slug: str) -> str:
    today = date.today().isoformat()
    text = re.sub(r"(?m)^- Feature slug:\s*$", f"- Feature slug: {slug}", text)
    text = re.sub(r"(?m)^- Request date:\s*$", f"- Request date: {today}", text)
    return text


def _doc_has_unresolved_placeholders(text: str) -> bool:
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line in {"-", "- "}:
            return True
        if re.fullmatch(r"- [^:]+:\s*", line):
            return True
        if _is_blank_table_row(line):
            return True
    return False


def _is_blank_table_row(line: str) -> bool:
    if not (line.startswith("|") and line.endswith("|")):
        return False
    cells = [cell.strip() for cell in line.strip("|").split("|")]
    if not cells:
        return False
    if all(set(cell) <= {"-"} and cell for cell in cells):
        return False
    return all(cell == "" for cell in cells)


def _field_value(text: str, label: str) -> str:
    pattern = re.compile(rf"(?m)^-\s*{re.escape(label)}:\s*(.+?)\s*$")
    match = pattern.search(text)
    if not match:
        return ""
    value = match.group(1).strip().strip("`").strip()
    if "/" in value:
        return ""
    return re.sub(r"\s+", " ", value).upper()


def _field_is_yes(text: str, label: str) -> bool:
    pattern = re.compile(rf"(?m)^-\s*{re.escape(label)}:\s*(.+?)\s*$")
    match = pattern.search(text)
    if not match:
        return False
    value = match.group(1).strip().strip("`").strip().lower()
    if "/" in value:
        return False
    return value in YES_VALUES


def _section_text(text: str, heading: str) -> str:
    pattern = re.compile(
        rf"(?ms)^##\s+{re.escape(heading)}\s*\n(?P<body>.*?)(?=^##\s+|\Z)"
    )
    match = pattern.search(text)
    if not match:
        return ""
    body = match.group("body").strip()
    return body


def _table_rows_in_section(text: str, heading: str) -> list[tuple[str, ...]]:
    section = _section_text(text, heading)
    rows: list[tuple[str, ...]] = []
    for raw_line in section.splitlines():
        line = raw_line.strip()
        if not (line.startswith("|") and line.endswith("|")):
            continue
        cells = tuple(cell.strip() for cell in line.strip("|").split("|"))
        if not cells:
            continue
        if all(set(cell) <= {"-"} and cell for cell in cells):
            continue
        if all(cell == "" for cell in cells):
            continue
        if cells[0].lower() in {"severity", "priority", "case", "command"}:
            continue
        rows.append(cells)
    return rows


def _row_is_none(row: tuple[str, ...]) -> bool:
    compact = " ".join(cell.strip().lower() for cell in row if cell.strip())
    return compact in NONE_VALUES or compact.startswith("none ")


def _content_is_none(text: str) -> bool:
    compact_lines = [
        line.strip().strip("-").strip().lower()
        for line in text.splitlines()
        if line.strip()
    ]
    compact_lines = [line for line in compact_lines if line]
    if not compact_lines:
        return True
    return all(line in NONE_VALUES for line in compact_lines)


def _normalize_repo_path(path_text: str) -> str:
    path = Path(path_text)
    if path.is_absolute():
        try:
            return path.resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            return path.as_posix()
    return path.as_posix().lstrip("./")


def _is_core_path(path_text: str) -> bool:
    return any(fnmatch.fnmatch(path_text, pattern) for pattern in _core_path_patterns())


def _is_production_path(path_text: str) -> bool:
    return any(fnmatch.fnmatch(path_text, pattern) for pattern in _production_path_patterns())


def _core_path_patterns() -> tuple[str, ...]:
    return _load_generated_patterns("core_paths.txt", DEFAULT_CORE_PATH_PATTERNS)


def _production_path_patterns() -> tuple[str, ...]:
    return _load_generated_patterns("production_paths.txt", DEFAULT_PRODUCTION_PATH_PATTERNS)


def _load_generated_patterns(filename: str, defaults: tuple[str, ...]) -> tuple[str, ...]:
    path = GENERATED_ROOT / filename
    if not path.exists():
        return defaults
    patterns = tuple(
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    )
    return patterns or defaults


def _display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def print_result(result: GuardResult) -> None:
    if result.ok:
        print("PASS")
    else:
        print("BLOCKED")
    for note in result.notes:
        print(f"NOTE: {note}")
    for warning in result.warnings:
        print(f"WARN: {warning}")
    for error in result.errors:
        print(f"ERROR: {error}")


if __name__ == "__main__":
    sys.exit(main())


def _make_executable(path: Path) -> None:
    """Set executable permission for the hook script."""
    import stat

    current = path.stat().st_mode
    path.chmod(current | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)