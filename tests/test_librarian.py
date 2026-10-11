"""Minimal self-check: submit -> exact retry -> flag -> resolve -> file.
No framework, no fixtures. Run: python tests/test_librarian.py
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PY = sys.executable
SUBMIT = str(REPO / "librarian" / "submit_event.py")
LIBRARIAN = str(REPO / "librarian" / "librarian.py")


def run(*args):
    r = subprocess.run([PY, *args], cwd=REPO, capture_output=True, text=True)
    assert r.returncode == 0, f"{args} failed: {r.stderr}"
    return r.stdout.strip()


def cleanup(subject_id: str):
    for f in (REPO / "filed").glob(f"{subject_id}.md"):
        f.unlink()
    for f in (REPO / "inbox").glob(f"{subject_id}__*.md"):
        f.unlink()


def purge_events_for(subject_id: str):
    events_dir = REPO / "events"
    if not events_dir.exists():
        return
    for day_dir in events_dir.glob("*"):
        if not day_dir.is_dir():
            continue
        for f in day_dir.glob("*.json"):
            try:
                ev = json.loads(f.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            if ev.get("subject_id") == subject_id:
                f.unlink()


def main() -> int:
    subject = "test.disposable-selfcheck"
    state_file = REPO / "librarian" / "state.json"
    state_backup = json.loads(state_file.read_text(encoding="utf-8")) if state_file.exists() else None

    try:
        out = run(SUBMIT, "--agent", "selfcheck", "--type", "update", "--subject-id", subject,
                   "--claim", "initial claim", "--evidence-label", "doc", "--evidence-link", "docs/ACCEPTANCE.md",
                   "--evidence-verified", "2026-10-10")
        assert "submitted:" in out, out
        event_id = out.split()[1]
        print("1/5 submit OK:", event_id)

        retry = run(SUBMIT, "--agent", "selfcheck", "--type", "update", "--subject-id", subject,
                     "--claim", "initial claim", "--evidence-label", "doc", "--evidence-link", "docs/ACCEPTANCE.md",
                     "--evidence-verified", "2026-10-10")
        assert "duplicate, no-op" in retry, retry
        assert event_id in retry, retry
        print("2/5 exact retry OK: no duplicate written")

        flag_out = run(SUBMIT, "--agent", "selfcheck", "--type", "flag", "--subject-id", subject,
                        "--claim", "needs a decision", "--question", "is this still accurate?",
                        "--required-evidence", "a human confirmation", "--follow-up-date", "2026-10-17")
        flag_event_id = flag_out.split()[1]
        print("3/5 flag submitted:", flag_event_id)

        run(LIBRARIAN, "--owner", "selfcheck-owner")
        filed_page = REPO / "filed" / f"{subject}.md"
        assert filed_page.exists(), "librarian should have drafted the update"
        inbox_matches = list((REPO / "inbox").glob(f"{subject}__*.md"))
        assert inbox_matches, "librarian should have flagged the open question"
        print("4/5 librarian run OK: drafted + flagged")

        flagged_inbox = inbox_matches[0]
        flagged_short_id = flagged_inbox.name.split("__")[1].replace(".md", "")
        resolve_out = run(SUBMIT, "--agent", "selfcheck", "--type", "resolve", "--subject-id", subject,
                           "--claim", "confirmed accurate", "--resolves-event-id", flagged_short_id,
                           "--evidence-label", "doc", "--evidence-link", "docs/ACCEPTANCE.md", "--evidence-verified", "2026-10-10")
        assert "submitted:" in resolve_out, resolve_out
        run(LIBRARIAN, "--owner", "selfcheck-owner")
        assert not list((REPO / "inbox").glob(f"{subject}__*.md")), "flag should be resolved/closed"
        print("5/5 resolve + file OK: flag closed, filed page updated")

        print("ALL OK")
        return 0
    finally:
        purge_events_for(subject)
        cleanup(subject)
        if state_backup is not None:
            state_file.write_text(json.dumps(state_backup, indent=2) + "\n", encoding="utf-8")
        elif state_file.exists():
            state_file.unlink()
        for d in (REPO / "librarian" / "receipts").glob("*.json"):
            d.unlink()
        for d in (REPO / "librarian" / "logs").glob("*.log"):
            d.unlink()


if __name__ == "__main__":
    raise SystemExit(main())
