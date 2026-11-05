#!/usr/bin/env python3
"""
Export one real day of Karnataka APMC rows into the two CSVs this room reads.

The rows come from KRAMA, the Karnataka state APMC price portal, as Negilu
ingested them: the `prices_kramahistoricstaging` table holds the feed *before*
canonicalisation, which is the stage where the faults this room exists to catch
are still visible. Nothing here is invented or adjusted.

The exported CSVs are committed to this repository, so the room runs from a
clean clone with no database. This script is here for provenance, and so the
day can be re-exported or a different one chosen.

    python tools/export_day.py --db /path/to/negilu.sqlite3 --date 2026-06-04

Without --db it looks for a Negilu checkout beside this one.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sqlite3
import statistics
import sys
from datetime import date, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT_OUT = REPO / "fixtures"

# The crops Negilu actually publishes. Rows for anything else are dropped, so
# the export stays the size of a real working day for this product rather than
# the whole state's trade.
NEGILU_CROPS = [
    "Arecanut", "Banana", "Banana Green", "Black Pepper", "Chilli", "Coconut",
    "Copra", "Green Chilly", "Green Ginger", "Groundnut", "Jowar", "Maize",
    "Mango", "Onion", "Paddy", "Ragi", "Rice", "Silk Cocoon", "Sunflower",
    "Tender Coconut", "Tomato", "Tur",
]

HISTORY_WINDOW_DAYS = 30

HEADER_RAW = [
    "date", "crop", "variety_raw", "grade", "mandi", "district",
    "arrivals_quintal", "min_price", "max_price", "modal_price",
]
HEADER_HISTORY = [
    "crop", "grade", "window_days", "rows",
    "min_modal", "max_modal", "median_modal", "median_arrivals",
]


def find_default_db() -> Path | None:
    for guess in (
        Path("D:/krishimitra_gpt/db.sqlite3"),
        REPO.parent.parent / "krishimitra_gpt" / "db.sqlite3",
        REPO.parent.parent / "krishimitra" / "db.sqlite3",
    ):
        if guess.exists():
            return guess
    return None


def load_canonicaliser(negilu_root: Path | None):
    """Use Negilu's own variety canonicaliser when we can reach it.

    It is what turns a raw feed label into the grade the site publishes, so
    using it keeps the `grade` column honest. Without it we fall back to a
    cleaned-up label, and say so.
    """
    if negilu_root and (negilu_root / "prices" / "variety_canon.py").exists():
        sys.path.insert(0, str(negilu_root))
        try:
            from prices.variety_canon import canonical_variety  # type: ignore
            return canonical_variety, True
        except Exception as exc:  # pragma: no cover - diagnostic only
            print(f"  ! could not import variety_canon ({exc}); using fallback")
    return (lambda commodity, variety: None), False


_SUFFIX = re.compile(r"\s*\[[^\]]*\]\s*$")


def fallback_grade(variety_raw: str) -> str:
    """Strip the feed's trailing qualifier, e.g. 'Pachha Bale [Average]'."""
    return _SUFFIX.sub("", (variety_raw or "")).strip() or "Unknown"


def base_crop(crop: str) -> str:
    """'COMMODITY: Banana' -> 'Banana', for crop filtering only.

    The exported `crop` column keeps the broken label: that leak is one of the
    faults, and repairing it here would hide the thing the room is for.
    """
    return re.sub(r"^COMMODITY:\s*", "", crop or "").strip()


def district_map(conn: sqlite3.Connection) -> dict[str, str]:
    """Market name -> district, preferring a real district to the placeholder."""
    out: dict[str, str] = {}
    rows = conn.execute("select name, district from prices_apmcmarket")
    for name, district in rows:
        if not name:
            continue
        key = name.strip().upper()
        district = (district or "").strip()
        if not district:
            continue
        # 'Karnataka' is the unresolved placeholder in Negilu's market table.
        if key in out and out[key] != "Karnataka":
            continue
        if key not in out or district != "Karnataka":
            out[key] = district
    return out


def export(db: Path, day: str, out_dir: Path, negilu_root: Path | None) -> None:
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    canonical_variety, have_canon = load_canonicaliser(negilu_root)
    districts = district_map(conn)
    wanted = {c.lower() for c in NEGILU_CROPS}

    def grade_for(crop: str, variety_raw: str) -> str:
        canon = canonical_variety(base_crop(crop), variety_raw)
        return canon or fallback_grade(variety_raw)

    # ---- raw_prices.csv : one real day, exactly as the feed gave it ---------
    day_rows = []
    query = """
        select date, commodity, variety, market, arrivals,
               min_price, max_price, modal_price
        from prices_kramahistoricstaging
        where date = ?
        order by commodity, market, variety
    """
    for d, crop, variety_raw, mandi, arrivals, lo, hi, modal in conn.execute(query, (day,)):
        if base_crop(crop).lower() not in wanted:
            continue
        day_rows.append({
            "date": d,
            "crop": crop,
            "variety_raw": variety_raw or "",
            "grade": grade_for(crop, variety_raw or ""),
            "mandi": mandi or "",
            "district": districts.get((mandi or "").strip().upper(), ""),
            "arrivals_quintal": "" if arrivals is None else int(round(float(arrivals))),
            "min_price": lo if lo is not None else "",
            "max_price": hi if hi is not None else "",
            "modal_price": modal if modal is not None else "",
        })

    out_dir.mkdir(parents=True, exist_ok=True)
    raw_path = out_dir / "raw_prices.csv"
    with raw_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=HEADER_RAW)
        writer.writeheader()
        writer.writerows(day_rows)

    # ---- price_history.csv : the 30 days before it, per crop and grade -----
    end = date.fromisoformat(day) - timedelta(days=1)
    start = end - timedelta(days=HISTORY_WINDOW_DAYS - 1)
    buckets: dict[tuple[str, str], dict[str, list]] = {}
    hist_query = """
        select date, commodity, variety, modal_price, arrivals
        from prices_kramahistoricstaging
        where date between ? and ? and modal_price is not null
    """
    for d, crop, variety_raw, modal, arrivals in conn.execute(
        hist_query, (start.isoformat(), end.isoformat())
    ):
        crop_clean = base_crop(crop)
        if crop_clean.lower() not in wanted:
            continue
        key = (crop_clean, grade_for(crop, variety_raw or ""))
        b = buckets.setdefault(key, {"modal": [], "arrivals": [], "days": set()})
        b["modal"].append(float(modal))
        if arrivals is not None:
            b["arrivals"].append(float(arrivals))
        b["days"].add(d)

    # Only keep grades that actually appear in the exported day, so the two
    # files line up and the reproducer never reports a band for a row that
    # is not there.
    present = {(base_crop(r["crop"]), r["grade"]) for r in day_rows}

    hist_rows = []
    for (crop, grade), b in sorted(buckets.items()):
        if (crop, grade) not in present or not b["modal"]:
            continue
        hist_rows.append({
            "crop": crop,
            "grade": grade,
            "window_days": HISTORY_WINDOW_DAYS,
            "rows": len(b["days"]),
            "min_modal": int(round(min(b["modal"]))),
            "max_modal": int(round(max(b["modal"]))),
            "median_modal": int(round(statistics.median(b["modal"]))),
            "median_arrivals": int(round(statistics.median(b["arrivals"]))) if b["arrivals"] else "",
        })

    hist_path = out_dir / "price_history.csv"
    with hist_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=HEADER_HISTORY)
        writer.writeheader()
        writer.writerows(hist_rows)

    missing = sum(1 for r in day_rows if (base_crop(r["crop"]), r["grade"]) not in
                  {(h["crop"], h["grade"]) for h in hist_rows})
    print(f"  {raw_path.relative_to(REPO)}: {len(day_rows)} rows for {day}")
    print(f"  {hist_path.relative_to(REPO)}: {len(hist_rows)} bands "
          f"over {start} .. {end}")
    print(f"  grade column from Negilu's canonicaliser: {have_canon}")
    if missing:
        print(f"  note: {missing} rows have no 30-day band (new or renamed grade)")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", type=Path, default=None,
                    help="SQLite database holding prices_kramahistoricstaging")
    ap.add_argument("--date", default="2026-06-04",
                    help="the day to export (default: the day shipped with this repo)")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--negilu-root", type=Path, default=None,
                    help="Negilu checkout, for its variety canonicaliser")
    args = ap.parse_args()

    db = args.db or find_default_db()
    if not db or not Path(db).exists():
        print("No Negilu database found. Pass --db /path/to/db.sqlite3.\n"
              "The exported CSVs are committed, so you do not need one to run "
              "the room — this script is for re-exporting a different day.",
              file=sys.stderr)
        return 1

    negilu_root = args.negilu_root or Path(db).resolve().parent
    print(f"Exporting {args.date} from {db}")
    export(Path(db), args.date, args.out, negilu_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
