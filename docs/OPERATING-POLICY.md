---
id: operating-policy
title: Operating Policy
owner: template
scope: template
status: published
---

# Operating Policy

## Default: human review before publication

Nothing an agent submits goes live on its own. The librarian only ever writes to `filed/`
(drafts) or `inbox/` (open questions). Promotion from `filed/` to `published/` is a manual
step (`librarian/publish.py`) run by the accountable owner or someone they've delegated to.
This is the default for every company instantiated from this template. An owner can change
it in `config/company.yml` (`publication_mode: human_review` is the only mode this template
ships with; a future `auto_publish_below_risk` mode is out of scope here — add it explicitly
if you need it, don't assume it exists).

## Who can do what

- **Any connected agent** may read `published/` and `wiki/`, and may submit events
  (`update`, `flag`, `resolve`) via `librarian/submit_event.py`.
- **No agent** edits `wiki/`, `filed/`, or `published/` directly. Pages change only through
  the event → librarian → draft → human-publish pipeline.
- **The accountable owner** (`config/company.yml: owner`) is who the librarian addresses
  every flag to, unless an event names a different owner for that specific page.
- **The librarian job** (see `docs/SCHEDULING.md`) runs unattended on a schedule. It only
  ever drafts or flags — it never publishes, pushes to a remote without review, or deletes
  an event.

## Source of truth stays where it already lives

This brain does not duplicate content that already has an authoritative home. Two rules:

1. **Source-code contracts stay authoritative for their own subjects.** If a fact is
   "what does this function/config/API actually do," the code is the source of truth — the
   brain links to the file and line, verified against a specific commit, and does not copy
   the logic into prose that can drift out of sync.
2. **The work tracker stays authoritative for task/ticket state.** If a fact is "is this
   done, who's doing it, what's blocking it," the work tracker (issue tracker, ledger, board
   — whatever `config/company.yml` names) is the source of truth. The brain may summarize
   and link to it, but never becomes a second place to check status.

A page that violates either rule should be flagged, not drafted.

## Scope discipline

Every page declares an explicit `scope` in its frontmatter. A page about one source
(e.g. a specific repo) does not grow sections about a different source's internals "while
we're at it." If an event's claim doesn't fit any existing page's scope, the librarian flags
it with a question — "which page should this live on, or does it need a new one" — rather
than guessing.

## Flagging over guessing

If an event lacks a resolvable source link, a verified date, or a clear owner, or if it
contradicts something already published, the librarian flags it in `inbox/` instead of
drafting a change. A flag names: an owner, a precise question, what evidence would resolve
it, and a follow-up date. The librarian never invents a fact or a source to avoid flagging.
