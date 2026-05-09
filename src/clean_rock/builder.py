import json
import shutil
import time
from pathlib import Path

from . import db, repo, stats

_CONTENT_TYPE = {
    ".html": "text/html",
    ".json": "application/json",
    ".css": "text/css",
    ".js": "application/javascript",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".svg": "image/svg+xml",
}


def build(
    database_path: Path,
    site_dir: Path,
    web_dir: Path,
    s3_bucket: str | None = None,
    cloudfront_distribution_id: str | None = None,
) -> None:
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

    # Mirror static assets so site_dir is a self-contained build artifact for S3.
    _mirror(web_dir / "public", site_dir / "assets" / "public", exclude={"index.html.template"})
    _mirror(web_dir / "images", site_dir / "assets" / "images")

    if s3_bucket:
        _publish_to_s3(site_dir, s3_bucket)
    if cloudfront_distribution_id:
        _invalidate_cloudfront(cloudfront_distribution_id)


def _mirror(src: Path, dst: Path, exclude: set[str] | None = None) -> None:
    if not src.exists():
        return
    skip = exclude or set()
    dst.mkdir(parents=True, exist_ok=True)
    for entry in src.iterdir():
        if entry.name in skip:
            continue
        if entry.is_dir():
            _mirror(entry, dst / entry.name, skip)
        else:
            shutil.copyfile(entry, dst / entry.name)


def _publish_to_s3(site_dir: Path, bucket: str) -> None:
    import boto3

    s3 = boto3.client("s3")
    for path in site_dir.rglob("*"):
        if not path.is_file():
            continue
        key = path.relative_to(site_dir).as_posix()
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=path.read_bytes(),
            ContentType=_CONTENT_TYPE.get(path.suffix.lower(), "application/octet-stream"),
        )


def _invalidate_cloudfront(distribution_id: str) -> None:
    import boto3

    cf = boto3.client("cloudfront")
    cf.create_invalidation(
        DistributionId=distribution_id,
        InvalidationBatch={
            "Paths": {"Quantity": 1, "Items": ["/*"]},
            "CallerReference": str(int(time.time() * 1000)),
        },
    )
