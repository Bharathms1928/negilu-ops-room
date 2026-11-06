# Negilu Incident Room — Flip the Switch (Track 01)

A person reports that mandi prices on [negilukrishi.in](https://negilukrishi.in)
look wrong. Two agents and that person close the incident together in one
Discord channel, connected by Switch.

Negilu is a Kannada-first market price service for farmers in Karnataka. Prices
come from KRAMA, the state APMC feed. Farmers read those numbers to decide when
to sell a harvest, so a wrong price is not a cosmetic bug — and that is why the
human sign-off in this room cannot be automated away.

## Why Switch

Remove Switch and three things stop working, none of which a bot or a webhook
replaces:

**No agent can approve its own work.** `negilu-triager` owns the `incident-log`
room document. `negilu-repro` can argue in the room but cannot write to that
document, cannot approve, and cannot close an incident. The split is enforced by
Switch's document ownership, not by our code choosing to behave.

**The reproducer is not addressable by people.** It is declared
`addressing: owner-agents`, so it answers only when the triager hands it work.
It is a step in a pipeline, not a chatbot someone can talk past.

**Decisions accumulate.** `incident-log` is a Switch room document on the server.
The triager checks it before classifying, so a repeat symptom is recognised as a
repeat rather than investigated from scratch. A private one-on-one agent chat
forgets everything between sessions.

## Architecture

```
People  ⇄  Discord #negilu-incidents  ⇄  Switch  ⇄  negilu-triager
                                                 ⇄  negilu-repro
                                        Switch room document: incident-log
```

## Agents

| Name | Addressable by | Role |
|---|---|---|
| `negilu-triager` | anyone | Restates, classifies (`data-bug` / `pipeline` / `genuine-move`), routes by name, owns `incident-log` |
| `negilu-repro` | owner agents only | Proves it against the day's rows, reports exact output, drafts the smallest fix. Cannot approve, cannot write the log |
| you | — | Approve, correct, decide |

Both agents run on the machine hosting the Switch server — on Windows that
means locally, under Git Bash; see the note under Quick start. The second
teammate takes part as a human in Discord.

## Quick start

**Prerequisites.** [Switch Console](https://github.com/sandbox-quantum/switch/releases/latest)
(v0.40.1 or later), a Switch server — the local one Console sets up is fine, and
on Windows it needs no Docker — a Discord server you can add a bot to, and a
coding agent signed in (Codex, Claude Code or OpenCode) with your own
subscription or key.

> **Windows users, read this first.** Agents do run on Windows: Console starts
> them locally under **Git Bash**, so neither Docker nor WSL is required. Spell
> the fixtures path the way Git Bash sees it —
> `/d/SwitchHackathon/negilu-ops-room/fixtures`, never `D:\...` and never
> `/mnt/d/...`.
>
> One Console quirk to expect in step 3: while **Location** is `local`, every
> provider card may read “Not supported here” and leave **Create** disabled. If
> that happens, register a POSIX SSH host under **Settings → Remote hosts**
> (WSL2 with `sshd` on a spare port is enough) and write its alias as the
> `location` default in the template — registered hosts never appear in the
> Location picker itself. That satisfies the provider check; the agent is still
> placed on this computer and still runs under Git Bash, so keep the Git Bash
> path. Console installs Git, Node and the agent CLI on a remote host for you
> but does not sign the agent in: do that yourself over SSH once.

1. Clone this repository.

2. Connect Discord in Console: **Home → Messaging apps → Connect → Discord**.
   The bot needs the `bot` and `applications.commands` scopes, and these
   permissions: View Channels, Send Messages, Send Messages in Threads, **Manage
   Webhooks**, Manage Channels, Manage Roles, Read Message History, Attach
   Files, Add Reactions. Manage Webhooks is what lets each agent post under its
   own name instead of all of them appearing as one bot.

   *Discord does not tell Switch when a bot joins a channel — a channel has no
   Switch room until somebody posts an ordinary message in it.*

3. **Templates** → load [`templates/negilu-ops.template.yaml`](templates/negilu-ops.template.yaml).
   Set **Fixtures folder** to the absolute path of this repo's `fixtures/`
   folder. Create.

4. Switch creates `#negilu-incidents` with both agents and you in it, then posts
   the kickoff.

## Demo script

Type these, in order. This is exactly what the demo video shows.

```
1.  @negilu-triager arecanut arrivals look way too high today — BANTWALA
    is showing the same lot more than once. Can you check?

2.  (triager restates, classifies, routes to @negilu-repro)

3.  (repro reads fixtures/raw_prices.csv and fixtures/price_history.csv,
     checks is_valid first, and reports that 33 duplicate groups survive
     the pipeline's own filter — 2,187,176 quintals published against a
     real 2,010,424, an 8.8% overstatement — then drafts the fix)

4.  approved — de-duplicate on mandi+grade before publishing, and log it

5.  (triager appends the outcome to the incident-log room document)
```

Two more real incidents are in the same file if you want to show the room
handling a repeat:

```
@negilu-triager some rows are coming through with the crop called
  "COMMODITY: Arecanut" — is the whole batch broken?
@negilu-triager arecanut at HOSADURGA says ₹1,700 a quintal. That cannot
  be right, can it?
```

## Fixtures

**Real rows, not samples.** `fixtures/raw_prices.csv` is one real day —
4 June 2026 — of Karnataka APMC prices from KRAMA, the state portal, as Negilu
ingested them before canonicalisation. Nothing is planted.

Each row carries `is_valid`, Negilu's own verdict on it. 433 of the 671 rows
were accepted and 238 were already rejected by the pipeline — and telling those
apart is most of the work. Among the accepted rows, 33 duplicate groups survive
and overstate the day's arrivals by **8.8%**; a price sits in the arrivals
column at ARAKALGUD; and arecanut at HOSADURGA publishes ₹1,700 against
₹26,300–32,649 everywhere else. Those three are live. The 220 rows with
`COMMODITY: Arecanut` as the crop name, by contrast, are already caught.

[`fixtures/README.md`](fixtures/README.md) documents each fault with the rows
that prove it. [`tools/export_day.py`](tools/export_day.py) produced the files,
for anyone who wants a different day. The CSVs are committed, so no database
and no credentials are needed to run the room.

## Layout

```
templates/negilu-ops.template.yaml   the room, both agents, their instructions
tools/export_day.py                  re-export a real day from a Negilu database
fixtures/raw_prices.csv              one real day of APMC rows, 671 of them
                                     with Negilu's own is_valid verdict on each
fixtures/price_history.csv           30-day bands per crop and grade
fixtures/community_feedback.csv      community comments (not used by this room)
fixtures/README.md                   what is wrong with that day, and how to tell
```

The agents' behaviour lives entirely in the template's `instructions:` blocks.
There is no application code in this repository: the room is the program.

## Track

01 — Best Business Workflow.

## Licence

MIT. The price fixtures are real public APMC data; see `fixtures/README.md`.
