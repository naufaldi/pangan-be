import contextlib
import time
import os
from typing import AsyncGenerator
from sqlalchemy import text
from app.infra.db import get_engine

_ready = False


def is_ready() -> bool:
    return _ready


@contextlib.asynccontextmanager
async def lifespan_context(app) -> AsyncGenerator[None, None]:
    global _ready
    # startup
    tz = os.environ.get("TZ", "Asia/Jakarta")
    try:
        os.environ["TZ"] = tz
    except Exception:
        pass
    # small warmup
    time.sleep(0.1)
    # Light DB warmup if DATABASE_URL provided (no schema creation here)
    try:
        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        # DATABASE_URL might be unset or DB unavailable; skip warmup
        pass
    _ready = True
    yield
    # shutdown
    _ready = False
