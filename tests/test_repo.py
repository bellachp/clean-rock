from datetime import date

from clean_rock import db, repo


def test_seed_and_list_bowlers(tmp_settings):
    db.init(tmp_settings.database_path)
    with db.connect(tmp_settings.database_path) as conn:
        repo.seed_bowlers(conn, ["A", "B", "C"])
        # Re-seeding is idempotent.
        repo.seed_bowlers(conn, ["A", "B", "C"])
        bowlers = repo.list_bowlers(conn)
    assert [b["name"] for b in bowlers] == ["A", "B", "C"]
    assert [b["display_order"] for b in bowlers] == [0, 1, 2]


def test_upsert_score_replaces_existing(tmp_settings):
    db.init(tmp_settings.database_path)
    with db.connect(tmp_settings.database_path) as conn:
        repo.seed_bowlers(conn, ["A"])
        bowler_id = repo.list_bowlers(conn)[0]["id"]
        repo.upsert_score(conn, date(2026, 1, 1), bowler_id, 150)
        repo.upsert_score(conn, date(2026, 1, 1), bowler_id, 200)
        rows = repo.fetch_games_long(conn)
    assert len(rows) == 1
    assert rows[0]["score"] == 200


def test_delete_score(tmp_settings):
    db.init(tmp_settings.database_path)
    with db.connect(tmp_settings.database_path) as conn:
        repo.seed_bowlers(conn, ["A"])
        bid = repo.list_bowlers(conn)[0]["id"]
        repo.upsert_score(conn, date(2026, 1, 1), bid, 150)
        repo.delete_score(conn, date(2026, 1, 1), bid)
        assert repo.fetch_games_long(conn) == []


def test_recent_weeks(tmp_settings):
    db.init(tmp_settings.database_path)
    with db.connect(tmp_settings.database_path) as conn:
        repo.seed_bowlers(conn, ["A", "B"])
        a, b = [b["id"] for b in repo.list_bowlers(conn)]
        repo.upsert_score(conn, date(2026, 1, 1), a, 100)
        repo.upsert_score(conn, date(2026, 1, 8), a, 110)
        repo.upsert_score(conn, date(2026, 1, 8), b, 200)
        recent = repo.fetch_recent_weeks(conn, limit=2)
    assert [w["game_date"] for w in recent] == ["2026-01-08", "2026-01-01"]
    assert recent[0]["scores"] == {"A": 110, "B": 200}
    assert recent[1]["scores"] == {"A": 100, "B": None}
