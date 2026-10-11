# Agent Instructions

You are an agent with read/submit access to this company brain. Before you act on anything
in this repo's domain:

1. Read `START-HERE.md`, then `docs/OPERATING-POLICY.md` and `docs/ACCEPTANCE.md`.
2. Read the relevant page(s) under `published/` for what you're about to touch. If there's
   no published page yet, check `wiki/` and `filed/`, but treat drafts as unreviewed.

After any meaningful update, submit exactly one event — don't edit `wiki/`, `filed/`, or
`published/` yourself:

```
python librarian/submit_event.py --agent "<your name>" --type update \
  --subject-id "<page id>" --claim "<what's true now>" \
  --evidence-label "<what>" --evidence-link "<path or URL>" --evidence-verified "<YYYY-MM-DD>"
```

If you're unsure whether a claim is true, or you have no resolvable source + verified date,
submit a `flag` instead of an `update`:

```
python librarian/submit_event.py --agent "<your name>" --type flag \
  --subject-id "<page id>" --claim "<what you observed>" \
  --question "<precise question>" --required-evidence "<what would resolve it>" \
  --follow-up-date "<YYYY-MM-DD>"
```

A librarian job (unattended, draft-only) turns events into drafts in `filed/` or flags in
`inbox/`. A human promotes drafts to `published/`. You will not see your update reflected in
`published/` immediately — that's by design (see `docs/OPERATING-POLICY.md`).
