import json
import shutil
from pathlib import Path

from . import db, repo, stats


def build(database_path: Path, site_dir: Path, web_dir: Path) -> None:
    site_dir.mkdir(parents=True, exist_ok=True)

    with db.connect(database_path) as conn:
        bowlers = repo.list_bowlers(conn)
        games_long = repo.fetch_games_long(conn)

    bowler_order = [b["name"] for b in bowlers]
    df = stats.games_to_df(games_long)
    ma_df = stats.trailing_ma(df)

    data = {
        "bowlers": bowler_order,
        "summary": stats.summary_table(df, ma_df, bowler_order),
        "raw": stats.wide_table(df, bowler_order),
    }
    (site_dir / "data.json").write_text(json.dumps(data, indent=2))
    (site_dir / "chart.json").write_text(json.dumps(stats.chart_spec(ma_df), indent=2))

    template = web_dir / "public" / "index.html.template"
    shutil.copyfile(template, site_dir / "index.html")
