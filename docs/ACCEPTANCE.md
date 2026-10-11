---
id: acceptance
title: Acceptance Criteria
owner: template
scope: template
status: published
---

# Acceptance Criteria

## Page frontmatter (required on every `wiki/`, `filed/`, `published/` page)

| Field      | Meaning                                                              |
|------------|-----------------------------------------------------------------------|
| `id`       | Stable, lowercase, dot-separated identifier. Never reused or changed once published. |
| `title`    | Human-readable title. |
| `owner`    | Who is accountable for this page's accuracy. |
| `source`   | List of `{label, link}` the page's claims are drawn from. At least one. |
| `verified` | ISO date the current content was last checked against its source(s). |
| `scope`    | One sentence: what this page is and is not about. |
| `status`   | `draft` (in `filed/`) or `published` (in `published/`). |

A page missing any field fails acceptance. The librarian will not draft it; it flags the
missing field instead.

## Event schema (one immutable JSON file per event, under `events/YYYY-MM-DD/`)

```json
{
  "event_id": "uuid4",
  "timestamp": "2026-10-10T13:00:00Z",
  "agent": "who/what submitted this",
  "type": "update | flag | resolve",
  "subject_id": "the wiki page id this concerns",
  "claim": "what changed, or what's true now",
  "evidence": [{"label": "...", "link": "...", "verified": "2026-10-10"}],
  "question": "only for type=flag",
  "required_evidence": "only for type=flag",
  "follow_up_date": "only for type=flag, ISO date",
  "resolves_event_id": "only for type=resolve"
}
```

Rules:

- **Immutable.** Once written, an event file is never edited or deleted. A correction is a
  new event.
- **`update` requires evidence.** At least one `evidence` entry, each with a resolvable
  `link` (a file path that exists, a URL that resolves, or a git ref that resolves) and a
  `verified` date. No evidence → the librarian auto-converts it to a flag.
- **Exact retry is a no-op.** `submit_event.py` hashes `(agent, type, subject_id, claim,
  evidence)` — if an identical event already exists, it returns the existing `event_id`
  instead of writing a duplicate. Retrying a submission after a network blip must be safe.
- **`flag` requires `question`, `required_evidence`, and `follow_up_date`.**
- **`resolve` requires `resolves_event_id`** pointing at an existing flag, plus the same
  evidence requirement as `update`.

## Librarian run (one pass)

A run is acceptable if, for every unprocessed event, exactly one of these happened and was
recorded in that run's receipt log (`librarian/receipts/`):

1. **Drafted** — evidence checked out, a `filed/<subject_id>.md` was written or updated,
   frontmatter passes the table above.
2. **Flagged** — evidence or a required field was missing/unresolvable; an `inbox/` entry
   was written with owner, question, required evidence, follow-up date.
3. **Resolved** — a `resolve` event matched an open `inbox/` entry; the inbox entry was
   closed and the corresponding `filed/` page updated.
4. **Skipped (duplicate)** — the event's content hash matched one already processed.

A run never publishes (`published/` is untouched), never deletes an event, and is idempotent
— running it again on the same event set changes nothing further.

## End-to-end proof (what "it works" means here)

Before this instance is considered built, run and record all five of:
`submit → exact retry (no duplicate) → flag → resolve → file (draft appears in filed/)`,
separate from the unit test suite — i.e. actually invoke `submit_event.py` and
`librarian.py` against a disposable subject, not just `pytest`.
