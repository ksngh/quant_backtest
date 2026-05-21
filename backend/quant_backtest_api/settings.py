from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class AppSettings:
    database_url: str | None
    cors_origins: tuple[str, ...]
    env: str

    @property
    def db_configured(self) -> bool:
        return bool(self.database_url)


def load_settings() -> AppSettings:
    raw_cors = os.getenv("BACKTEST_API_CORS_ORIGINS", "")
    cors_origins = tuple(part.strip() for part in raw_cors.split(",") if part.strip())
    return AppSettings(
        database_url=os.getenv("DATABASE_URL"),
        cors_origins=cors_origins,
        env=os.getenv("BACKTEST_API_ENV", "dev"),
    )
