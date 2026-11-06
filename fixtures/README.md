# Fixtures

**These are real rows.** `raw_prices.csv` is one real day — **4 June 2026** —
of Karnataka APMC market prices from KRAMA, the state price portal, exactly as
Negilu ingested them. Nothing is invented, adjusted or planted. The faults
below are faults the live feed actually had that day.

They are committed so that anyone cloning this repo gets the same room and the
same incidents, with no database and no credentials. To export a different day,
see [`tools/export_day.py`](../tools/export_day.py).

## Files

| File | Read by | What it is |
|---|---|---|
| `raw_prices.csv` | triager, repro | 671 rows — one real day, before canonicalisation |
| `price_history.csv` | repro only | 116 bands — per crop and grade, the 30 days to 3 June 2026 |
| `community_feedback.csv` | neither, for now | Community comments in English, Kannada and transliterated Kannada |

The split in that middle row is deliberate. The triager can see today's prices
but not what they *should* be, so it cannot settle a price complaint on its own
and has to hand it to the reproducer. That is the room working as designed.

`community_feedback.csv` is the one synthetic file here, written for a second
workflow that is not built.

## Read `is_valid` before you believe anything

`raw_prices.csv` carries two columns that are Negilu's own verdict on each row:

| Column | Meaning |
|---|---|
| `is_valid` | `1` if Negilu's pipeline accepted the row, `0` if it already rejected it |
| `validation_notes` | why, when the pipeline said so |

**433 of the 671 rows are valid; 238 were already rejected.** Rejected rows are
exported rather than filtered out on purpose: a fault the pipeline already
catches is a completely different problem from one that slipped through, and
telling them apart is most of the job. An agent that reports the raw totals
without checking `is_valid` will overstate every fault here by roughly a
factor of five. That trap is deliberate.

`price_history.csv`, by contrast, is built from **valid rows only** — a band
computed over rejected rows is not what the product believes a crop is worth.

## What is actually wrong with this day

Each of these is reproducible from the committed CSVs.

### Already caught by Negilu — verify, do not re-report

1. **Broken crop labels — 220 rows, all `is_valid=0`.** The feed emitted
   `COMMODITY: Arecanut`, `COMMODITY: Tomato`, `COMMODITY: Banana` and others
   as the *crop name*. Negilu's phantom-commodity guard rejects every one of
   them, and the guard's own source comment names this exact date. A third of
   the file looks broken and is already handled.

### Not caught — these are live

2. **Duplicate rows the guard does not collapse.** Among valid rows alone,
   33 groups are the same trade reported twice, and summing arrivals naively
   gives 2,187,176 quintals where the real figure is 2,010,424 — an **8.8%
   overstatement**. Arrivals drive the "market is flooded, hold back" signal a
   farmer acts on, so an 8.8% error is a real one.
   *(Across all 671 rows the same measure reads 45.6%. That number is wrong to
   quote: most of it is rows Negilu already throws away.)*

3. **Column smear.** `Arecanut,Sippegotu [Medium],ARAKALGUD,Hassan` reads
   `12800,12800,12800,12800` — arrivals equal to min, max and modal. Every
   other Sippegotu lot that day is 26–227 quintals, and 12,800 sits inside the
   Sippegotu *price* range of ₹11,000–13,700, so the price was copied into the
   arrivals column. `is_valid=1`: nothing catches it, and it alone adds 12,800
   phantom quintals.

   This one was not written up by us. `negilu-repro` found it while proving
   fault 2, generalised it into a feed-wide test — *arrivals == min == max ==
   modal* — and reported that exactly one row matches.

4. **Implausible price.** Arecanut Coca at HOSADURGA, ₹1,700 a quintal, against
   ₹26,300–32,649 at every other Coca mandi that day. `is_valid=1`. ×10 lands
   it at ₹17,000, inside the band and alongside BANTWALA's minimum, so it looks
   like a decimal fault rather than one bad row.

5. **Thin arrivals.** 12 valid rows rest on 2 quintals or fewer. One lot is not
   a market rate.

6. **Bands that are not bands.** 10 of the 116 bands have fewer than six
   observations or zero width — `Arecanut/Podi` has exactly one. Podi and Pudi
   are the same commodity under two spellings, so the split leaves Podi with a
   one-point "band" and HOSADURGA's perfectly ordinary ₹9,020 falls outside it.
   **A band gate without a minimum-observations floor will quarantine good
   rows.** Also found by the reproducer, unprompted.

**The stale-feed check has nothing to catch here.** Every row is dated
2026-06-04. That is how a clean day looks on that axis, and the reproducer
should say so rather than inventing something.

## Re-exporting

```
python tools/export_day.py --db /path/to/negilu.sqlite3 --date 2026-06-04
```

The script reads `prices_kramahistoricstaging`, keeps only the crops Negilu
publishes, resolves each mandi's district, derives the `grade` column with
Negilu's own `variety_canon.py`, and carries `is_valid` through. It writes both
CSVs in place.

You need a Negilu database for that. You do **not** need one to run this room —
the exported CSVs are committed.

**Do not commit an export containing anything the public feed does not already
publish**, and never commit credentials. See `.gitignore`.
