import os
import sys
from pathlib import Path
from typing import Tuple

import pytest
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

TEST_DB_PATH = Path(__file__).resolve().parent / "test_runtime.db"
os.environ.setdefault("DATABASE_URL", f"sqlite:///{TEST_DB_PATH}")
os.environ.setdefault("JWT_SECRET", "test_secret")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test_bot_token")
os.environ.setdefault("JWT_EXPIRES_MINUTES", "60")
os.environ.setdefault("JWT_REFRESH_DAYS", "7")

MODULES_TO_RESET = [
    "db",
    "auth",
    "deps",
    "main",
    "core.jwt",
    "routers.auth",
    "routers.protocols",
    "services.defi_data",
    "services.agent",
]


def _reset_db(base, engine) -> None:
    with engine.begin() as conn:
        base.metadata.drop_all(conn)
        base.metadata.create_all(conn)


def _load_app() -> Tuple[object, object, object]:
    for module in MODULES_TO_RESET:
        sys.modules.pop(module, None)
    from db import Base, engine
    from main import app

    _reset_db(Base, engine)
    return app, engine, Base


@pytest.fixture(scope="session")
def app():
    app, engine, _base = _load_app()
    yield app
    engine.dispose()


@pytest.fixture(autouse=True)
def reset_database():
    from db import Base, engine

    _reset_db(Base, engine)
    yield


@pytest.fixture
def client(app):
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
