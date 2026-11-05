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

That day's feed genuinely duplicated 496 of its 671 rows across commodity
labels, inflating the day's arrivals by 46%; emitted `COMMODITY: Arecanut` as
a crop name in 220 rows; and priced arecanut at HOSADURGA nineteen times under
the day's median. [`fixtures/README.md`](fixtures/README.md) documents each
fault with the rows that prove it, including one apparent fault that turns out
not to be one.

This is a bug in a product with real users, found by pointing the room at its
own data. [`tools/export_day.py`](tools/export_day.py) is the script that
produced the files.

## Checklist before submitting

- [x] Public repo that runs from a clean clone
- [x] README with setup steps and an explicit section on how Switch is used
- [x] Agent template committed, so the room can be recreated in one step
- [x] Fixtures committed, so no database or credentials are needed
- [ ] Demo video showing the room, both agents and the human decision point
- [ ] Video link added to the top of this file
- [ ] README followed once from a clean clone by the teammate who did not build it

Submissions close **7 November 2026, 11:59 PM IST**.
