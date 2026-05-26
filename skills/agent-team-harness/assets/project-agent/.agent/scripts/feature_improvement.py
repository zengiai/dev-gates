#!/usr/bin/env python3
"""Create a post-feature improvement note from durable feature documents."""

from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path
from typing import Sequence


REPO_ROOT = Path(__file__).resolve().parents[2]
FEATURE_ROOT = REPO_ROOT / "docs" / "features"
IMPROVEMENT_ROOT = REPO_ROOT / ".agent" / "improvements"
FEATURE_DOCS = (
    "01_REQUIREMENT_ANALYSIS.md",
    "02_SOLUTION_DESIGN.md",
    "03_GATE_REVIEW.md",
    "04_DEVELOPMENT.md",
    "05_CODE_REVIEW.md",
    "06_TEST_REPORT.md",
)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a reusable improvement note from feature documents.")
    parser.add_argument("slug", help="StableEnglishPascalCase feature slug")
    args = parser.parse_args(argv)

    slug = args.slug
    if not re.fullmatch(r"[A-Z][A-Za-z0-9]*", slug):
        raise SystemExit("slug must use StableEnglishPascalCase")

    feature_dir = FEATURE_ROOT / slug
    if not feature_dir.exists():
        raise SystemExit(f"feature folder does not exist: {feature_dir}")

    docs = {name: _read(feature_dir / name) for name in FEATURE_DOCS}
    missing = [name for name, text in docs.items() if not text]
    output = _build_note(slug, docs, missing)
    target = IMPROVEMENT_ROOT / f"{slug}_IMPROVEMENT.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(output, encoding="utf-8")
    print(f"wrote {target.relative_to(REPO_ROOT)}")
    print("Review this note before changing .agent materials or role skills.")
    return 0


def _read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _build_note(slug: str, docs: dict[str, str], missing: Sequence[str]) -> str:
    reusable_signals = _collect_signals(docs)
    missing_text = "\n".join(f"- {name}" for name in missing) if missing else "- None"
    signal_text = "\n".join(f"- {item}" for item in reusable_signals) if reusable_signals else "- None detected automatically. Review the feature manually."
    return f"""# Feature Improvement Note

## Feature

- Feature slug: {slug}
- Generated date: {date.today().isoformat()}

## Missing Documents

{missing_text}

## Reusable Signals Found

{signal_text}

## Candidate Team Material Updates

- `.agent/materials/project-code-profile.md`:
- `.agent/materials/code-style-guide.md`:
- `.agent/materials/templates/FEATURE_DEVELOPMENT_TEMPLATE.md`:
- `.agent/materials/templates/BUGFIX_TEMPLATE.md`:
- `.agent/materials/templates/LANGUAGE_CODE_PATTERNS.md`:
- `.agent/materials/checklists/CHANGE_REVIEW_CHECKLIST.md`:
- `.agent/templates/feature-docs/`:
- `.agent/skill-teams/project-dev-team/`:
- `.agent/rule.md`:

## Review Decision

- Update team materials: `yes` / `no`
- Reason:
- Reviewer:

## Rules

- Update reusable team materials only for repeatable patterns.
- Do not promote one-off workaround into a team rule without documenting risk.
- Keep improvement patches small and reviewable.
- If this feature exposed missing language coverage, add a follow-up role proposal instead of inventing a partial specialist silently.
"""


def _collect_signals(docs: dict[str, str]) -> list[str]:
    signals: list[str] = []
    keywords = (
        "Residual Risks",
        "Must-Fix Items",
        "Defects",
        "Deviations",
        "Rollback",
        "Performance / Load Test Need",
        "Open Questions",
        "Required Additions",
    )
    for name, text in docs.items():
        for keyword in keywords:
            section = _section_text(text, keyword)
            if section and not _content_is_empty(section):
                first_line = next((line.strip("- ").strip() for line in section.splitlines() if line.strip()), "")
                if first_line:
                    signals.append(f"{name} / {keyword}: {first_line[:180]}")
    return signals


def _section_text(text: str, heading: str) -> str:
    pattern = re.compile(rf"(?ms)^##\s+{re.escape(heading)}\s*\n(?P<body>.*?)(?=^##\s+|\Z)")
    match = pattern.search(text)
    return match.group("body").strip() if match else ""


def _content_is_empty(text: str) -> bool:
    compact = [line.strip().strip("-").strip().lower() for line in text.splitlines() if line.strip()]
    compact = [line for line in compact if line and set(line) != {"|"}]
    return not compact or all(line in {"none", "n/a", "na", "no", "无"} for line in compact)


if __name__ == "__main__":
    raise SystemExit(main())

