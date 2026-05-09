from contextlib import asynccontextmanager
from datetime import date

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from . import auth, builder, config, db, repo

settings = config.get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init(settings.database_path)
    builder.build(
        settings.database_path,
        settings.site_dir,
        settings.web_dir,
        s3_bucket=settings.s3_bucket,
        cloudfront_distribution_id=settings.cloudfront_distribution_id,
    )
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,
    session_cookie="cleanrock_session",
    https_only=False,
    same_site="lax",
)


# ---- Admin HTML pages (cookie-gated) ----

@app.get("/admin/login")
def admin_login_page() -> FileResponse:
    return FileResponse(settings.web_dir / "admin" / "login.html")


@app.get("/admin")
def admin_page(request: Request):
    if not auth.is_admin(request):
        return RedirectResponse("/admin/login", status_code=303)
    return FileResponse(settings.web_dir / "admin" / "index.html")


# ---- Admin API ----

@app.post("/api/admin/login")
def login(request: Request, password: str = Form(...)):
    if password != settings.admin_password:
        return RedirectResponse("/admin/login?error=1", status_code=303)
    request.session["admin"] = True
    return RedirectResponse("/admin", status_code=303)


@app.post("/api/admin/logout")
def logout(request: Request):
    request.session.pop("admin", None)
    return RedirectResponse("/admin/login", status_code=303)


@app.get("/api/admin/bowlers", dependencies=[Depends(auth.require_admin)])
def get_bowlers():
    with db.connect(settings.database_path) as conn:
        return repo.list_bowlers(conn)


@app.get("/api/admin/recent", dependencies=[Depends(auth.require_admin)])
def get_recent(limit: int = 5):
    with db.connect(settings.database_path) as conn:
        return repo.fetch_recent_weeks(conn, limit=limit)


@app.post("/api/admin/scores", dependencies=[Depends(auth.require_admin)])
async def post_scores(request: Request):
    form = await request.form()
    raw_date = form.get("game_date")
    if not raw_date:
        raise HTTPException(status_code=400, detail="game_date required")
    try:
        game_date = date.fromisoformat(str(raw_date))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"invalid game_date: {e}")

    with db.connect(settings.database_path) as conn:
        bowlers = repo.list_bowlers(conn)
        for b in bowlers:
            field = f"score_{b['id']}"
            value = form.get(field)
            if value is None or str(value).strip() == "":
                # Absence: ensure no stale row exists for this (date, bowler).
                repo.delete_score(conn, game_date, b["id"])
                continue
            try:
                score = int(value)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"invalid score for {b['name']}")
            if not 0 <= score <= 900:
                raise HTTPException(status_code=400, detail=f"score out of range for {b['name']}")
            repo.upsert_score(conn, game_date, b["id"], score)

    builder.build(
        settings.database_path,
        settings.site_dir,
        settings.web_dir,
        s3_bucket=settings.s3_bucket,
        cloudfront_distribution_id=settings.cloudfront_distribution_id,
    )

    if "application/json" in request.headers.get("accept", ""):
        return JSONResponse({"ok": True})
    return RedirectResponse("/admin?ok=1", status_code=303)


# ---- Static mounts (registered last so explicit routes win) ----

# site_dir + web_dir may not exist yet on first run; check_dir=False defers the check.
app.mount(
    "/assets/public",
    StaticFiles(directory=str(settings.web_dir / "public"), check_dir=False),
    name="public-assets",
)
app.mount(
    "/assets/images",
    StaticFiles(directory=str(settings.web_dir / "images"), check_dir=False),
    name="image-assets",
)
app.mount(
    "/",
    StaticFiles(directory=str(settings.site_dir), html=True, check_dir=False),
    name="site",
)
