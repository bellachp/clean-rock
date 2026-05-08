import json

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_settings):
    # Reset the FastAPI module so it reads the test settings on import.
    import importlib

    import clean_rock.main as main_mod
    main_mod = importlib.reload(main_mod)
    with TestClient(main_mod.app) as c:
        yield c


def _login(client, password="test-pw"):
    return client.post(
        "/api/admin/login",
        data={"password": password},
        follow_redirects=False,
    )


def test_admin_redirects_when_not_logged_in(client):
    r = client.get("/admin", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/admin/login"


def test_login_success_then_admin_loads(client):
    r = _login(client)
    assert r.status_code == 303
    assert r.headers["location"] == "/admin"
    r = client.get("/admin", follow_redirects=False)
    assert r.status_code == 200
    assert b"Add scores" in r.content


def test_login_failure_redirects_with_error(client):
    r = _login(client, password="wrong")
    assert r.status_code == 303
    assert r.headers["location"] == "/admin/login?error=1"


def test_unauthorized_api_calls_get_401(client):
    assert client.get("/api/admin/recent").status_code == 401
    assert client.get("/api/admin/bowlers").status_code == 401
    assert (
        client.post("/api/admin/scores", data={"game_date": "2026-01-01"}).status_code == 401
    )


def test_score_write_triggers_rebuild(client, tmp_settings):
    from clean_rock import db, repo
    db.init(tmp_settings.database_path)
    with db.connect(tmp_settings.database_path) as conn:
        repo.seed_bowlers(conn, ["A", "B", "C", "D", "E", "F"])
        bowlers = repo.list_bowlers(conn)

    _login(client)
    form = {"game_date": "2026-01-01"}
    for i, b in enumerate(bowlers):
        form[f"score_{b['id']}"] = str(150 + i * 5)
    r = client.post("/api/admin/scores", data=form, follow_redirects=False)
    assert r.status_code == 303

    data = json.loads((tmp_settings.site_dir / "data.json").read_text())
    assert data["bowlers"] == [b["name"] for b in bowlers]
    assert data["raw"][0]["game_date"] == "2026-01-01"
    assert data["raw"][0]["scores"]["A"] == 150
    assert data["raw"][0]["scores"]["F"] == 175

    chart = json.loads((tmp_settings.site_dir / "chart.json").read_text())
    assert any(v["bowler"] == "A" for v in chart["data"]["values"])


def test_blank_score_means_absence(client, tmp_settings):
    from clean_rock import db, repo
    db.init(tmp_settings.database_path)
    with db.connect(tmp_settings.database_path) as conn:
        repo.seed_bowlers(conn, ["A", "B"])
        bowlers = repo.list_bowlers(conn)

    _login(client)
    form = {
        "game_date": "2026-02-05",
        f"score_{bowlers[0]['id']}": "180",
        f"score_{bowlers[1]['id']}": "",  # absent
    }
    r = client.post("/api/admin/scores", data=form, follow_redirects=False)
    assert r.status_code == 303

    with db.connect(tmp_settings.database_path) as conn:
        rows = repo.fetch_games_long(conn)
    assert len(rows) == 1
    assert rows[0]["bowler"] == "A"
