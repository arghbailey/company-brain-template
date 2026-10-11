---
id: scheduling
title: Scheduling
owner: template
scope: template
status: published
---

# Scheduling

The librarian is meant to run unattended, on a cadence set in `config/company.yml`
(`librarian.cadence`, `librarian.timezone`). It must be wired into whatever native
recurring-job system already exists on the machine it runs on — don't introduce a new
scheduler (e.g. don't add cron on a box that uses Windows Task Scheduler, or vice versa)
and don't guess the command for that scheduler; inspect what's actually installed and how
existing jobs on this machine are already defined, then match that pattern.

## Requirements for the job, whatever the scheduler

1. **Own folder/namespace.** Don't drop it alongside unrelated jobs; group it so it's easy
   to find and disable as a set.
2. **Bounded runtime.** Set a hard time limit on the run. A librarian pass over a normal
   event volume should finish in well under a minute; cap it generously above that, not
   unbounded.
3. **No overlap.** If a run is still going when the next trigger fires, skip the new one —
   never stack concurrent librarian runs against the same `events/`/`filed/`/`inbox/` state.
4. **Don't collide with other jobs.** Check what else is already scheduled on this machine
   (times, resource use) before picking a time slot.
5. **Use existing secret storage.** If the librarian ever needs a credential (it doesn't,
   by default — everything here is local files plus whatever `git`/`gh` auth already exists
   on the box), pull it from whatever secret store the other jobs on this machine already
   use. Don't invent a new one.
6. **Log every run** to `librarian/logs/`, and keep the run's receipt in
   `librarian/receipts/` per `docs/ACCEPTANCE.md`.
7. **Publish within granted authority.** The scheduled run only ever drafts/flags — it must
   never be configured to call `librarian/publish.py`. Publication stays a manual, reviewed
   step per `docs/OPERATING-POLICY.md`.

## What to record once the job exists

After registering the job, write down (in `config/company.yml` or this file's instance
copy):

- **Job ID / name** and which scheduler owns it.
- **Cadence and time zone** actually configured (not assumed).
- **Next run time** at the moment it was registered.
- **Exact command to disable it** (e.g. the one-liner to unregister/disable the job).

A saved prompt, goal file, or "I'll remember to run this" is not a scheduled job. Don't mark
this checkpoint done until the scheduler itself reports the job registered, and ideally until
one real execution (manually triggered or naturally fired) has been observed and logged.
