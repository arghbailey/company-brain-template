#!/usr/bin/env python3
"""Draft-only librarian pass. Reads events/, writes only to filed/ and inbox/.
Never touches published/. See docs/ACCEPTANCE.md and docs/OPERATING-POLICY.md.

Usage: librarian.py [--company config/company.yml]
"""
import argparse
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

REPO = Path(__file__).resolve().parent.parent
EVENTS = REPO / "events"
INBOX = REPO / "inbox"
FILED = REPO / "filed"
STATE = REPO / "librarian" / "state.json"
RECEIPTS = REPO / "librarian" / "receipts"
LOGS = REPO / "librarian" / "logs"
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)
REQUIRED_FIELDS = ["id", "title", "owner", "source", "verified", "scope", "status"]


def load_state() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {"processed_event_ids": []}


def save_state(state: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def all_events() -> list:
    if not EVENTS.exists():
        return []
    out = []
    for day_dir in sorted(EVENTS.iterdir()):
        if not day_dir.is_dir():
            continue
        for f in sorted(day_dir.glob("*.json")):
            try:
                out.append(json.loads(f.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, OSError):
                continue
    return out


def evidence_resolves(link: str) -> bool:
    parsed = urlparse(link)
    if parsed.scheme in ("http", "https"):
        return True  # ponytail: format-only check, no live fetch from a scheduled job; upgrade if dead links become a real problem
    p = Path(link)
    if not p.is_absolute():
        p = REPO / link
    return p.exists()


def evidence_ok(evidence: list) -> tuple:
    if not evidence:
        return False, "no evidence provided"
    for e in evidence:
        if not e.get("link") or not e.get("verified"):
            return False, f"evidence entry missing link or verified date: {e}"
        if not evidence_resolves(e["link"]):
            return False, f"evidence link does not resolve: {e['link']}"
    return True, ""


def write_flag(owner: str, event: dict, question: str, required_evidence: str, follow_up_date: str, receipt: list) -> None:
    INBOX.mkdir(parents=True, exist_ok=True)
    out = INBOX / f"{event['subject_id']}__{event['event_id'][:8]}.md"
    out.write_text(
        "---\n"
        f"owner: {owner}\n"
        f"subject_id: {event['subject_id']}\n"
        f"source_event_id: {event['event_id']}\n"
        f"follow_up_date: {follow_up_date}\n"
        "status: open\n"
        "---\n\n"
        f"# Flag: {event['subject_id']}\n\n"
        f"**Question:** {question}\n\n"
        f"**Required evidence:** {required_evidence}\n\n"
        f"**Original claim:** {event.get('claim', '')}\n",
        encoding="utf-8",
    )
    receipt.append({"event_id": event["event_id"], "action": "flagged", "path": str(out.relative_to(REPO))})


def draft_page(event: dict, receipt: list) -> None:
    FILED.mkdir(parents=True, exist_ok=True)
    out = FILED / f"{event['subject_id']}.md"
    today = datetime.now(timezone.utc).date().isoformat()
    source_lines = "\n".join(
        f"  - label: {e.get('label', '')}\n    link: {e['link']}\n    verified: {e['verified']}" for e in event["evidence"]
    )
    if out.exists():
        m = FRONTMATTER_RE.match(out.read_text(encoding="utf-8"))
        body = m.group(2) if m else ""
    else:
        body = f"\n# {event['subject_id']}\n"
    body += f"\n- {today} ({event['agent']}): {event['claim']}\n"
    out.write_text(
        "---\n"
        f"id: {event['subject_id']}\n"
        f"title: {event['subject_id']}\n"
        f"owner: {event.get('owner', 'unassigned')}\n"
        "source:\n"
        f"{source_lines}\n"
        f"verified: {today}\n"
        "scope: drafted by librarian, review scope before publishing\n"
        "status: draft\n"
        "---\n"
        f"{body}",
        encoding="utf-8",
    )
    receipt.append({"event_id": event["event_id"], "action": "drafted", "path": str(out.relative_to(REPO))})


def resolve_flag(event: dict, receipt: list) -> bool:
    target_id = event["resolves_event_id"][:8]
    matches = list(INBOX.glob(f"*__{target_id}.md"))
    if not matches:
        return False
    draft_page(event, receipt)
    for m in matches:
        m.unlink()
    receipt.append({"event_id": event["event_id"], "action": "resolved", "closed": [str(m.name) for m in matches]})
    return True


def run(company_owner: str = "unassigned") -> dict:
    state = load_state()
    processed = set(state["processed_event_ids"])
    receipt = []
    counts = {"drafted": 0, "flagged": 0, "resolved": 0, "skipped_duplicate": 0}

    for event in all_events():
        eid = event["event_id"]
        if eid in processed:
            counts["skipped_duplicate"] += 1
            continue

        if event["type"] == "flag":
            write_flag(event.get("owner", company_owner), event, event["question"], event["required_evidence"], event["follow_up_date"], receipt)
            counts["flagged"] += 1
        elif event["type"] == "update":
            ok, reason = evidence_ok(event.get("evidence", []))
            if ok:
                draft_page(event, receipt)
                counts["drafted"] += 1
            else:
                follow_up = (datetime.now(timezone.utc) + timedelta(days=3)).date().isoformat()
                write_flag(company_owner, event, f"evidence unresolved: {reason}", "a resolvable link and a verified date", follow_up, receipt)
                counts["flagged"] += 1
        elif event["type"] == "resolve":
            ok, reason = evidence_ok(event.get("evidence", []))
            if ok and resolve_flag(event, receipt):
                counts["resolved"] += 1
            else:
                follow_up = (datetime.now(timezone.utc) + timedelta(days=3)).date().isoformat()
                write_flag(company_owner, event, f"resolve failed: {reason or 'no matching open flag'}", "a resolvable link, a verified date, and a matching open flag", follow_up, receipt)
                counts["flagged"] += 1

        processed.add(eid)

    state["processed_event_ids"] = sorted(processed)
    save_state(state)

    RECEIPTS.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    (RECEIPTS / f"{ts}.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    (LOGS / f"{ts}.log").write_text(
        f"{ts} run: drafted={counts['drafted']} flagged={counts['flagged']} resolved={counts['resolved']} skipped_duplicate={counts['skipped_duplicate']}\n",
        encoding="utf-8",
    )
    return counts


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--owner", default="unassigned", help="default owner for auto-generated flags")
    args = ap.parse_args()
    counts = run(company_owner=args.owner)
    print(f"drafted={counts['drafted']} flagged={counts['flagged']} resolved={counts['resolved']} skipped_duplicate={counts['skipped_duplicate']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
