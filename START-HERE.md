---
id: start-here
title: Start Here
owner: template
scope: template
status: published
---

# Company Brain — Start Here

This repo is a small, append-only knowledge base for one company, meant to be read and
updated by both humans and AI agents. It is NOT a chat log and NOT a dumping ground —
every page carries an owner, a source, and a verified date, and nothing gets published
without human review by default.

## Read these next, in order

1. `docs/OPERATING-POLICY.md` — who can publish what, and the default-to-human-review rule.
2. `docs/ACCEPTANCE.md` — what makes a page or an event "good enough" (required fields).
3. `docs/SCHEDULING.md` — how the librarian job runs and where to see/disable it.

## The shape of the repo

```
config/company.yml     one file: who this brain is for, who owns it, which sources/agents it covers
wiki/                   the actual knowledge pages (frontmatter + body)
events/                 append-only, immutable: one JSON file per submitted update/flag/resolve
inbox/                  open questions the librarian couldn't resolve on its own
filed/                  librarian's drafts — NOT yet reviewed by a human
published/              the only directory agents should treat as "true" and cite
librarian/              the script that turns events into drafts or flags
tests/                  the one test file proving submit/retry/flag/resolve/file works
```

## If you are an agent reading this

1. Read the relevant page(s) under `published/` (and `wiki/` for the raw source) before you
   act on anything in this domain. Don't trust your own memory of this company over what's
   published here.
2. After any meaningful update — something a human would want to know happened — submit
   ONE event with `librarian/submit_event.py`. Don't edit pages directly.
3. If you're not sure a claim is true, or you don't have a source link and a date you
   verified it, submit a `flag` instead of an `update`. Guessing is worse than asking.

## If you are a human

- New pages get drafted into `filed/` by the librarian. Review them, then run
  `librarian/publish.py <subject_id>` to promote a draft into `published/`.
- Open questions live in `inbox/` with an owner, a question, what evidence would resolve it,
  and a follow-up date. Resolve them by submitting a `resolve` event (see ACCEPTANCE.md).
