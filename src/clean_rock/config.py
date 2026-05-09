from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    admin_password: str = Field(default="change-me", alias="ADMIN_PASSWORD")
    session_secret: str = Field(default="dev-only-not-secret", alias="SESSION_SECRET")
    database_path: Path = Field(default=REPO_ROOT / "data" / "scores.db", alias="DATABASE_PATH")
    site_dir: Path = Field(default=REPO_ROOT / "site", alias="SITE_DIR")
    web_dir: Path = Field(default=REPO_ROOT / "web", alias="WEB_DIR")
    seeds_dir: Path = Field(default=REPO_ROOT / "seeds", alias="SEEDS_DIR")
    s3_bucket: str | None = Field(default=None, alias="CLEAN_ROCK_S3_BUCKET")
    cloudfront_distribution_id: str | None = Field(
        default=None, alias="CLEAN_ROCK_CLOUDFRONT_DISTRIBUTION_ID"
    )

    def resolve(self) -> "Settings":
        # Make relative paths absolute against repo root.
        for field in ("database_path", "site_dir", "web_dir", "seeds_dir"):
            value: Path = getattr(self, field)
            if not value.is_absolute():
                object.__setattr__(self, field, (REPO_ROOT / value).resolve())
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings().resolve()
