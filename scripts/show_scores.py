"""Print the contents of scores.db as a readable wide table.

Usage:
    uv run python scripts/show_scores.py
    uv run python scripts/show_scores.py --since 2026-01-01
    uv run python scripts/show_scores.py --limit 20
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from clean_rock import config, db, repo  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="View scores.db")
    parser.add_argument("--since", help="ISO date; show games on/after this date")
    parser.add_argument("--limit", type=int, help="Show only the N most-recent dates")
    args = parser.parse_args()

    settings = config.get_settings()
    if not settings.database_path.exists():
        raise SystemExit(f"No DB at {settings.database_path}. Run scripts/seed_bowlers.py first.")

    with db.connect(settings.database_path) as conn:
        bowlers = repo.list_bowlers(conn)
        games = repo.fetch_games_long(conn)

    print(f"Bowlers ({len(bowlers)}): " + ", ".join(b["name"] for b in bowlers))
    if not games:
        print("(no games yet)")
        return

    df = pd.DataFrame(games)
    if args.since:
        df = df[df["game_date"] >= args.since]
    bowler_order = [b["name"] for b in bowlers]
    wide = (
        df.pivot_table(index="game_date", columns="bowler", values="score", aggfunc="first")
        .reindex(columns=bowler_order)
        .sort_index(ascending=False)
    )
    if args.limit:
        wide = wide.head(args.limit)

    # Render integer scores as int and absences as blank cells.
    wide = wide.astype("Int64")
    display = wide.astype(object).where(wide.notna(), "")
    with pd.option_context("display.max_rows", None, "display.width", 200):
        print()
        print(display.to_string())
    print(f"\n{len(wide)} week(s); {df['score'].notna().sum()} score(s) total.")


if __name__ == "__main__":
    main()
