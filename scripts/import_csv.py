"""Import historical scores from a wide-format CSV (Google Sheet export).

Expected CSV layout:
    date,Bowler 1,Bowler 2,Bowler 3,Bowler 4,Bowler 5,Bowler 6
    2024-01-04,180,,210,165,,200
    ...

- The first column header must be `date` (case-insensitive); remaining headers
  must match bowler names already seeded in the DB.
- Blank cells = absence (no row inserted).
- Idempotent on (game_date, bowler_id): re-running updates scores in place.
"""

import argparse
import csv
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from clean_rock import config, db, repo  # noqa: E402


def _parse_date(s: str) -> date:
    s = s.strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%-m/%-d/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return date.fromisoformat(s)


def main() -> None:
    parser = argparse.ArgumentParser(description="Import wide CSV into scores DB")
    parser.add_argument("csv_path", type=Path)
    args = parser.parse_args()

    settings = config.get_settings()
    db.init(settings.database_path)

    with db.connect(settings.database_path) as conn:
        bowlers = repo.list_bowlers(conn)
    if not bowlers:
        raise SystemExit("No bowlers in DB. Run scripts/seed_bowlers.py first.")
    by_name = {b["name"]: b["id"] for b in bowlers}

    inserted = 0
    skipped = 0
    with args.csv_path.open(newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None or len(reader.fieldnames) < 2:
            raise SystemExit("CSV has no headers")
        date_col = reader.fieldnames[0]
        unknown = [c for c in reader.fieldnames[1:] if c not in by_name]
        if unknown:
            raise SystemExit(
                f"Unknown bowler columns: {unknown}. Either rename them or update seeds/bowlers.json."
            )
        with db.connect(settings.database_path) as conn:
            for row in reader:
                raw_date = row[date_col].strip()
                if not raw_date:
                    continue
                try:
                    game_date = _parse_date(raw_date)
                except ValueError as e:
                    print(f"  skip row, bad date {raw_date!r}: {e}", file=sys.stderr)
                    skipped += 1
                    continue
                for col_name in reader.fieldnames[1:]:
                    cell = (row.get(col_name) or "").strip()
                    if not cell:
                        continue
                    try:
                        score = int(cell)
                    except ValueError:
                        print(f"  skip {game_date} {col_name}: bad int {cell!r}", file=sys.stderr)
                        skipped += 1
                        continue
                    if not 0 <= score <= 900:
                        print(f"  skip {game_date} {col_name}: score {score} out of range", file=sys.stderr)
                        skipped += 1
                        continue
                    repo.upsert_score(conn, game_date, by_name[col_name], score)
                    inserted += 1
    print(f"Imported {inserted} score(s); skipped {skipped}.")


if __name__ == "__main__":
    main()
