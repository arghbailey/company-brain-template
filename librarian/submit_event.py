#!/usr/bin/env python3
"""Append one immutable event to events/YYYY-MM-DD/. See docs/ACCEPTANCE.md for the schema.

Usage:
  submit_event.py --agent NAME --type update --subject-id ID --claim TEXT \
      --evidence-label L --evidence-link URL --evidence-verified YYYY-MM-DD

  submit_event.py --agent NAME --type flag --subject-id ID --claim TEXT \
      --question Q --required-evidence R --follow-up-date YYYY-MM-DD

  submit_event.py --agent NAME --type resolve --subject-id ID --claim TEXT \
      --resolves-event-id UUID --evidence-label L --evidence-link URL --evidence-verified YYYY-MM-DD

Exact retry (same agent/type/subject/claim/evidence) is a no-op: prints the existing
event_id instead of writing a duplicate.
"""
import argparse
import hashlib
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
EVENTS = REPO / "events"


def content_hash(agent: str, type_: str, subject_id: str, claim: str, evidence: list) -> str:
    payload = json.dumps(
        {"agent": agent, "type": type_, "subject_id": subject_id, "claim": claim, "evidence": evidence},
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def find_existing(h: str):
    if not EVENTS.exists():
        return None
    for day_dir in EVENTS.iterdir():
        if not day_dir.is_dir():
            continue
        for f in day_dir.glob("*.json"):
            try:
                ev = json.loads(f.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            if ev.get("_content_hash") == h:
                return ev
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", required=True)
    ap.add_argument("--type", required=True, choices=["update", "flag", "resolve"])
    ap.add_argument("--subject-id", required=True)
    ap.add_argument("--claim", required=True)
    ap.add_argument("--evidence-label", action="append", default=[])
    ap.add_argument("--evidence-link", action="append", default=[])
    ap.add_argument("--evidence-verified", action="append", default=[])
    ap.add_argument("--question")
    ap.add_argument("--required-evidence")
    ap.add_argument("--follow-up-date")
    ap.add_argument("--resolves-event-id")
    args = ap.parse_args()

    if len(args.evidence_label) != len(args.evidence_link) or len(args.evidence_label) != len(args.evidence_verified):
        print("evidence-label/link/verified must all repeat the same number of times", file=sys.stderr)
        return 2

    evidence = [
        {"label": l, "link": lk, "verified": v}
        for l, lk, v in zip(args.evidence_label, args.evidence_link, args.evidence_verified)
    ]

    if args.type == "flag" and not (args.question and args.required_evidence and args.follow_up_date):
        print("flag requires --question --required-evidence --follow-up-date", file=sys.stderr)
        return 2
    if args.type == "resolve" and not args.resolves_event_id:
        print("resolve requires --resolves-event-id", file=sys.stderr)
        return 2

    h = content_hash(args.agent, args.type, args.subject_id, args.claim, evidence)
    existing = find_existing(h)
    if existing:
        print(f"duplicate, no-op: {existing['event_id']}")
        return 0

    now = datetime.now(timezone.utc)
    event = {
        "event_id": str(uuid.uuid4()),
        "timestamp": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "agent": args.agent,
        "type": args.type,
        "subject_id": args.subject_id,
        "claim": args.claim,
        "evidence": evidence,
        "_content_hash": h,
    }
    if args.type == "flag":
        event.update(question=args.question, required_evidence=args.required_evidence, follow_up_date=args.follow_up_date)
    if args.type == "resolve":
        event["resolves_event_id"] = args.resolves_event_id

    day_dir = EVENTS / now.strftime("%Y-%m-%d")
    day_dir.mkdir(parents=True, exist_ok=True)
    out = day_dir / f"{now.strftime('%H%M%S')}-{args.agent}-{event['event_id'][:8]}.json"
    out.write_text(json.dumps(event, indent=2) + "\n", encoding="utf-8")
    print(f"submitted: {event['event_id']} -> {out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
