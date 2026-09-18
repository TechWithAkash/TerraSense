import os
import tempfile
from pathlib import Path

# the app reads DATABASE_URL at import time (via get_settings), so this has to happen before
# anything under app/ gets imported - every eval/golden-scenario test runs against its own
# throwaway sqlite file, never the developer's local terrasense.db.
_TEST_DB_PATH = Path(tempfile.gettempdir()) / "terrasense_test.db"
_TEST_DB_PATH.unlink(missing_ok=True)
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB_PATH}"

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client
    _TEST_DB_PATH.unlink(missing_ok=True)
