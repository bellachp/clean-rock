import sqlite3
from datetime import date


def list_bowlers(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT id, name, display_order FROM bowlers ORDER BY display_order, name"
    ).fetchall()
    return [dict(r) for r in rows]


def seed_bowlers(conn: sqlite3.Connection, names: list[str]) -> None:
    for i, name in enumerate(names):
        conn.execute(
            "INSERT OR IGNORE INTO bowlers (name, display_order) VALUES (?, ?)",
            (name, i),
        )


def upsert_score(
    conn: sqlite3.Connection, game_date: date, bowler_id: int, score: int
) -> None:
    conn.execute(
        """
        INSERT INTO games (game_date, bowler_id, score)
        VALUES (?, ?, ?)
        ON CONFLICT(game_date, bowler_id) DO UPDATE SET score=excluded.score
        """,
        (game_date.isoformat() if isinstance(game_date, date) else game_date, bowler_id, score),
    )


def delete_score(conn: sqlite3.Connection, game_date: date, bowler_id: int) -> None:
    conn.execute(
        "DELETE FROM games WHERE game_date = ? AND bowler_id = ?",
        (game_date.isoformat() if isinstance(game_date, date) else game_date, bowler_id),
    )


def fetch_games_long(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        """
        SELECT g.game_date AS game_date,
               b.id        AS bowler_id,
               b.name      AS bowler,
               b.display_order AS display_order,
               g.score     AS score
        FROM games g
        JOIN bowlers b ON b.id = g.bowler_id
        ORDER BY g.game_date, b.display_order
        """
    ).fetchall()
    return [dict(r) for r in rows]


def fetch_recent_weeks(conn: sqlite3.Connection, limit: int = 5) -> list[dict]:
    """Return the N most-recent distinct game_dates with each bowler's score (or None)."""
    bowlers = list_bowlers(conn)
    dates = [
        r["game_date"]
        for r in conn.execute(
            "SELECT DISTINCT game_date FROM games ORDER BY game_date DESC LIMIT ?", (limit,)
        ).fetchall()
    ]
    if not dates:
        return []
    placeholders = ",".join("?" * len(dates))
    rows = conn.execute(
        f"""
        SELECT game_date, bowler_id, score
        FROM games
        WHERE game_date IN ({placeholders})
        """,
        dates,
    ).fetchall()
    by_date: dict[str, dict[int, int]] = {d: {} for d in dates}
    for r in rows:
        by_date[r["game_date"]][r["bowler_id"]] = r["score"]
    out = []
    for d in dates:
        out.append(
            {
                "game_date": d,
                "scores": {b["name"]: by_date[d].get(b["id"]) for b in bowlers},
            }
        )
    return out
