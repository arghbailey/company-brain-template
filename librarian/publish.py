#!/usr/bin/env python3
"""Manual-only promotion: filed/<subject_id>.md -> published/<subject_id>.md.
Never call this from the scheduled librarian run (see docs/OPERATING-POLICY.md).

Usage: publish.py <subject_id> [--force]
"""
import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FILED = REPO / "filed"
PUBLISHED = REPO / "published"
REQUIRED_FIELDS = ["id", "title", "owner", "source", "verified", "scope", "status"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("subject_id")
    ap.add_argument("--force", action="store_true", help="publish even if a required field looks empty")
    args = ap.parse_args()

    src = FILED / f"{args.subject_id}.md"
    if not src.exists():
        print(f"no draft at {src.relative_to(REPO)}", file=sys.stderr)
        return 1

    text = src.read_text(encoding="utf-8")
    missing = [f for f in REQUIRED_FIELDS if not re.search(rf"^{f}:\s*\S", text, re.MULTILINE)]
    if missing and not args.force:
        print(f"refusing to publish, missing/empty fields: {missing} (use --force to override)", file=sys.stderr)
        return 1

    text = re.sub(r"^status: draft$", "status: published", text, flags=re.MULTILINE)
    PUBLISHED.mkdir(parents=True, exist_ok=True)
    dst = PUBLISHED / f"{args.subject_id}.md"
    dst.write_text(text, encoding="utf-8")
    print(f"published: {dst.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
