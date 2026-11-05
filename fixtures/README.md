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
| `price_history.csv` | repro only | 121 bands — per crop and grade, the 30 days to 3 June 2026 |
| `community_feedback.csv` | neither, for now | Community comments in English, Kannada and transliterated Kannada |

The split in that middle row is deliberate. The triager can see today's prices
but not what they *should* be, so it cannot settle a price complaint on its own
and has to hand it to the reproducer. That is the room working as designed.

`community_feedback.csv` is the one synthetic file here, written for a second
workflow that is not built.

## Why "before canonicalisation"

Negilu's pipeline reads KRAMA into a staging table, then canonicalises variety
labels into the grades the site publishes. The rows here are from the staging
table, which is where a bad batch is still visible. By the time a row reaches
the public site it has been merged, de-duplicated and filtered — and a fault
that survives that is much harder to see.

## What is actually wrong with this day

Each of these is reproducible from the committed CSVs.

1. **Duplicate rows — the day's arrivals inflate by 46%.** 496 of the 671 rows
   are duplicates: one trade emitted under two or three commodity labels at
   once. Arecanut at BANTWALA appears as `Arecanut`, `Arecanut` and
   `COMMODITY: Arecanut`, all with 64 quintals at ₹26,300. Summing arrivals
   naively gives 2,935,051 quintals where the real figure is 2,015,169.
   For a farmer reading "arrivals are heavy, hold back", that is the whole
   decision, wrong.

2. **Broken crop labels — 220 rows.** The feed emitted `COMMODITY: Arecanut`,
   `COMMODITY: Tomato`, `COMMODITY: Banana` and others as the *crop name*. A
   third of the file. This is a broken batch, not a bad row, and the fix is
   different for each.

3. **Implausible price.** Arecanut Coca at HOSADURGA, ₹1,700 a quintal, against
   a same-day Arecanut median of ₹32,818 and ₹26,300 for the same grade at
   BANTWALA. Nineteen times too low — a unit mix-up or a parse error.

4. **Thin arrivals.** 25 rows rest on 2 quintals or fewer. Arecanut Api at
   CHITRADURGA sets ₹52,959 on a single quintal; one lot is not a market rate.

5. **Blank district.** Two rows carry a mandi the market table cannot place.

6. **Ripeness inversion.** At BINNY MILL (F&V), green Balekai is ₹2,100 against
   ripe Pachha Bale at ₹1,600. Worth knowing that this one is *not* obviously a
   fault: over the preceding 30 days Balekai's median is ₹2,771 and Pachha
   Bale's is ₹1,300, so in this market green trades above ripe routinely. It is
   in the room instructions as a check that the reproducer must test against
   history rather than assume — which is the point.

7. **Column shift.** One row reads
   `Arecanut,Sippegotu [Medium],ARAKALGUD,Hassan,12800,12800,12800,12800` —
   arrivals equal to the min, max and modal price. Every other Sippegotu lot
   that day is between 26 and 227 quintals, and 12,800 sits squarely inside
   the Sippegotu *price* range of ₹11,000–₹13,700. The price was copied into
   the arrivals column. On its own it adds 12,800 phantom quintals, and it is
   most of what is left of the arrivals anomaly once the duplicates are
   removed: Arecanut's total runs 3.78× its 30-day expectation with this row
   in and 1.50× with it out.

   This one was not written up by us. `negilu-repro` found it while proving
   fault 1, generalised it into a feed-wide test — *arrivals == min == max ==
   modal* — and reported that exactly one row in the day matches.

**The stale-feed check has nothing to catch here.** Every row is dated
2026-06-04. That is how a clean day looks on that axis, and the reproducer
should say so rather than inventing something.

## Re-exporting

```
python tools/export_day.py --db /path/to/negilu.sqlite3 --date 2026-06-04
```

The script reads `prices_kramahistoricstaging`, keeps only the crops Negilu
publishes, resolves each mandi's district, and derives the `grade` column with
Negilu's own `variety_canon.py` so it matches what the site would show. It
writes both CSVs in place.

You need a Negilu database for that. You do **not** need one to run this room —
the exported CSVs are committed.

**Do not commit an export containing anything the public feed does not already
publish**, and never commit credentials. See `.gitignore`.
