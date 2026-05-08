"""Seed the bowlers table from seeds/bowlers.json. Idempotent."""

import json
import sys
from pathlib import Path

# Allow `python scripts/seed_bowlers.py` from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from clean_rock import config, db, repo  # noqa: E402


def main() -> None:
    settings = config.get_settings()
    db.init(settings.database_path)
    names = json.loads((settings.seeds_dir / "bowlers.json").read_text())
    if not isinstance(names, list) or not all(isinstance(n, str) for n in names):
        raise SystemExit("seeds/bowlers.json must be a JSON array of strings")
    with db.connect(settings.database_path) as conn:
        repo.seed_bowlers(conn, names)
        bowlers = repo.list_bowlers(conn)
    print(f"Seeded; {len(bowlers)} bowler(s) in DB:")
    for b in bowlers:
        print(f"  {b['display_order']:>2}  {b['name']}  (id={b['id']})")


if __name__ == "__main__":
    main()
