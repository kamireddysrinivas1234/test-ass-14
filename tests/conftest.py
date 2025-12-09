import os
import sys
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

@pytest.fixture(autouse=True)
def _clean_db(tmp_path, monkeypatch):
    # Use a temp sqlite DB for every test run
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    yield
