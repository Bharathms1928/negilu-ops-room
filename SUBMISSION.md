# Submission — Flip the Switch, Track 01

**Project:** The Negilu Incident Room
**Track:** 01 — Best Business Workflow
**Team:** 2 people
**Repo:** https://github.com/Bharathms1928/negilu-ops-room
**Demo video:** _add the link here before submitting_

## What this is, in one line

A Discord channel, bridged by Switch, where two agents and a person close a
mandi-price incident for [negilukrishi.in](https://negilukrishi.in) — and no
decision is recorded until the person approves it.

## What Switch is doing that nothing else would

Three things, each enforced by Switch rather than by our code choosing to
behave. Remove Switch and all three stop.

1. **Document ownership.** `incident-log` belongs to `negilu-triager`.
   `negilu-repro` can argue in the room but cannot write that document,
   cannot approve and cannot close an incident.
2. **Addressing.** `negilu-repro` is declared `addressing: owner-agents`, so
   it answers only when the triager hands it work. It is a step in a pipeline,
   not a chatbot a person can talk past.
3. **Accumulated room state.** The triager reads `incident-log` before
   classifying, so a repeat symptom is recognised as a repeat. A private
   one-to-one agent chat forgets everything between sessions.

A fourth thing is designed rather than enforced, and matters as much: the
triager reads only `raw_prices.csv`, while the reproducer also reads
`price_history.csv`. The triager therefore **cannot** settle a price
complaint alone, however plausible a story it can tell. The handoff is
structural.

## What a judge needs to reproduce it

Everything is in this repo. No database, no credentials, no production access.

1. Switch Console v0.40.1 or later, a Switch server (the local one is fine),
   a Discord server you can add a bot to, and one coding agent signed in.
2. Load `templates/negilu-ops.template.yaml` under **Templates**, set
   **Fixtures folder** to this repo's `fixtures/`, and Create.
3. Post the first line of the demo script in the channel.

Full steps, including the two Windows quirks, are in [README.md](README.md).

## The data is real

`fixtures/raw_prices.csv` is one real day — 4 June 2026 — of Karnataka APMC
prices from KRAMA, the state portal, as Negilu ingested them before
canonicalisation. Nothing is planted.

Every row carries `is_valid`, Negilu's own verdict on it: 433 of the 671 were
accepted, 238 were already rejected by the pipeline. Separating the two is most
of the job, and an agent that skips it overstates every fault here about
fivefold.

Three faults are live, in rows the pipeline accepted: 33 duplicate groups that
overstate the day's arrivals by **8.8%**, a price sitting in the arrivals
column at ARAKALGUD, and arecanut at HOSADURGA publishing ₹1,700 against
₹26,300–32,649 everywhere else. A fourth — 220 rows with `COMMODITY: Arecanut`
as the crop name — is already caught by a guard whose source comment names this
exact date.

[`fixtures/README.md`](fixtures/README.md) documents each with the rows that
prove it, including one apparent fault that turns out not to be one.
[`tools/export_day.py`](tools/export_day.py) produced the files.

## Checklist before submitting

- [x] Public repo that runs from a clean clone
- [x] README with setup steps and an explicit section on how Switch is used
- [x] Agent template committed, so the room can be recreated in one step
- [x] Fixtures committed, so no database or credentials are needed
- [ ] Demo video showing the room, both agents and the human decision point
- [ ] Video link added to the top of this file
- [ ] README followed once from a clean clone by the teammate who did not build it

Submissions close **7 November 2026, 11:59 PM IST**.
