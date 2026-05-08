from typing import Any

import pandas as pd

MA_WINDOW = 10


def games_to_df(games_long: list[dict]) -> pd.DataFrame:
    if not games_long:
        return pd.DataFrame(columns=["game_date", "bowler", "display_order", "score"])
    df = pd.DataFrame(games_long)
    df["game_date"] = pd.to_datetime(df["game_date"]).dt.date
    return df


def trailing_ma(df: pd.DataFrame, window: int = MA_WINDOW) -> pd.DataFrame:
    """Per-bowler trailing moving average over their played games (skips absences)."""
    if df.empty:
        return df.assign(ma=pd.Series(dtype="float64"))
    df = df.sort_values(["bowler", "game_date"]).copy()
    df["ma"] = df.groupby("bowler")["score"].transform(
        lambda s: s.rolling(window=window, min_periods=1).mean()
    )
    return df


def wide_table(df: pd.DataFrame, bowler_order: list[str]) -> list[dict]:
    """One row per game_date, columns are bowler names. Absences = None."""
    if df.empty:
        return []
    pivot = df.pivot_table(
        index="game_date", columns="bowler", values="score", aggfunc="first"
    )
    # Ensure all bowler columns exist even if one has zero games.
    for name in bowler_order:
        if name not in pivot.columns:
            pivot[name] = pd.NA
    pivot = pivot[bowler_order]
    pivot = pivot.sort_index(ascending=False)  # newest first for the public table
    out = []
    for game_date, row in pivot.iterrows():
        scores = {}
        for name in bowler_order:
            v = row[name]
            scores[name] = None if pd.isna(v) else int(v)
        out.append({"game_date": game_date.isoformat(), "scores": scores})
    return out


def summary_table(df: pd.DataFrame, ma_df: pd.DataFrame, bowler_order: list[str]) -> list[dict]:
    if df.empty:
        return [
            {
                "bowler": name,
                "games": 0,
                "average": None,
                "current_ma10": None,
                "high": None,
                "low": None,
                "stddev": None,
            }
            for name in bowler_order
        ]
    out = []
    for name in bowler_order:
        sub = df[df["bowler"] == name]
        if sub.empty:
            out.append(
                {
                    "bowler": name,
                    "games": 0,
                    "average": None,
                    "current_ma10": None,
                    "high": None,
                    "low": None,
                    "stddev": None,
                }
            )
            continue
        latest_ma = ma_df[ma_df["bowler"] == name].sort_values("game_date").iloc[-1]["ma"]
        out.append(
            {
                "bowler": name,
                "games": int(len(sub)),
                "average": round(float(sub["score"].mean()), 2),
                "current_ma10": round(float(latest_ma), 2),
                "high": int(sub["score"].max()),
                "low": int(sub["score"].min()),
                "stddev": round(float(sub["score"].std(ddof=0)), 2) if len(sub) > 1 else 0.0,
            }
        )
    return out


def chart_spec(ma_df: pd.DataFrame) -> dict[str, Any]:
    """Vega-Lite spec: multi-line chart of trailing-10 MA per bowler."""
    if ma_df.empty:
        values: list[dict] = []
    else:
        values = [
            {
                "game_date": r["game_date"].isoformat() if hasattr(r["game_date"], "isoformat") else str(r["game_date"]),
                "bowler": r["bowler"],
                "ma": round(float(r["ma"]), 2),
            }
            for _, r in ma_df.iterrows()
        ]
    return {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "description": "10-game moving average per bowler",
        "width": "container",
        "height": 400,
        "data": {"values": values},
        "mark": {"type": "line", "point": True, "interpolate": "monotone"},
        "encoding": {
            "x": {"field": "game_date", "type": "temporal", "title": "Date"},
            "y": {
                "field": "ma",
                "type": "quantitative",
                "title": "10-game MA",
                "scale": {"zero": False},
            },
            "color": {"field": "bowler", "type": "nominal", "title": "Bowler"},
            "tooltip": [
                {"field": "game_date", "type": "temporal", "title": "Date"},
                {"field": "bowler", "type": "nominal"},
                {"field": "ma", "type": "quantitative", "format": ".1f"},
            ],
        },
    }
