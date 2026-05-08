from datetime import date

from clean_rock import stats


def _games(rows):
    """rows: list of (date, bowler, score)"""
    return [
        {"game_date": d, "bowler": b, "display_order": 0, "score": s}
        for (d, b, s) in rows
    ]


def test_trailing_ma_skips_absences():
    """A bowler's MA is over their last N played games, not last N weeks."""
    rows = _games(
        [
            (date(2026, 1, 1), "A", 100),
            (date(2026, 1, 8), "A", 200),
            (date(2026, 1, 15), "A", 150),
            # B was absent weeks 1+2; first played week 3.
            (date(2026, 1, 15), "B", 220),
        ]
    )
    df = stats.games_to_df(rows)
    ma = stats.trailing_ma(df, window=10)
    a_rows = ma[ma["bowler"] == "A"].sort_values("game_date")
    assert list(a_rows["ma"]) == [100.0, 150.0, 150.0]
    b_rows = ma[ma["bowler"] == "B"]
    assert list(b_rows["ma"]) == [220.0]


def test_trailing_ma_window():
    """11th game drops the 1st."""
    rows = _games([(date(2026, 1, i + 1), "A", 100 + i) for i in range(11)])
    df = stats.games_to_df(rows)
    ma = stats.trailing_ma(df, window=10)
    a = ma[ma["bowler"] == "A"].sort_values("game_date").reset_index(drop=True)
    # Last row is mean of scores 101..110 = 105.5
    assert abs(a.iloc[-1]["ma"] - 105.5) < 1e-9
    # Second-to-last is mean of 100..109 = 104.5
    assert abs(a.iloc[-2]["ma"] - 104.5) < 1e-9


def test_summary_table_basic():
    rows = _games(
        [
            (date(2026, 1, 1), "A", 100),
            (date(2026, 1, 8), "A", 200),
            (date(2026, 1, 1), "B", 150),
        ]
    )
    df = stats.games_to_df(rows)
    ma = stats.trailing_ma(df)
    summary = stats.summary_table(df, ma, ["A", "B"])
    a = next(s for s in summary if s["bowler"] == "A")
    assert a["games"] == 2
    assert a["average"] == 150.0
    assert a["high"] == 200
    assert a["low"] == 100
    b = next(s for s in summary if s["bowler"] == "B")
    assert b["games"] == 1
    assert b["stddev"] == 0.0


def test_summary_zero_games():
    df = stats.games_to_df([])
    ma = stats.trailing_ma(df)
    summary = stats.summary_table(df, ma, ["A", "B"])
    assert all(s["games"] == 0 and s["average"] is None for s in summary)


def test_wide_table_absences_are_none():
    rows = _games(
        [
            (date(2026, 1, 1), "A", 100),
            (date(2026, 1, 8), "B", 200),
        ]
    )
    df = stats.games_to_df(rows)
    wide = stats.wide_table(df, ["A", "B"])
    # Newest first.
    assert wide[0]["game_date"] == "2026-01-08"
    assert wide[0]["scores"] == {"A": None, "B": 200}
    assert wide[1]["scores"] == {"A": 100, "B": None}


def test_chart_spec_shape():
    rows = _games([(date(2026, 1, 1), "A", 100)])
    df = stats.games_to_df(rows)
    spec = stats.chart_spec(stats.trailing_ma(df))
    assert spec["data"]["values"][0]["bowler"] == "A"
    assert spec["mark"]["type"] == "line"
