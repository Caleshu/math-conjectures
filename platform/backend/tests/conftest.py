import os
import tempfile

import pytest

# Isolated SQLite database and data directory for every test session; never touches dev data.
_tmp = tempfile.mkdtemp(prefix="mrl-test-")
os.environ["DATA_DIR"] = _tmp
os.environ["DATABASE_URL"] = ""
os.environ["RUN_EMBEDDED_WORKER"] = "false"
os.environ["ANTHROPIC_API_KEY"] = ""
os.environ["OPENAI_API_KEY"] = ""
os.environ["CLAUDE_CODE_ENABLED"] = "false"  # tests must never call a real model
os.environ["REPO_EXPORT_ENABLED"] = "false"  # tests must never push to a real repository
os.environ["REQUIRE_AUTH"] = "false"


@pytest.fixture(scope="session", autouse=True)
def _db():
    from app.config import get_settings
    from app.db import Base, get_engine, reset_engine
    from app import models  # noqa: F401

    get_settings.cache_clear()
    reset_engine()
    Base.metadata.create_all(get_engine())
    yield


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as c:
        yield c
