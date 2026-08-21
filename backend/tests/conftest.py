import os

os.environ["MONGODB_DATABASE"] = "supplyx_test"
# Tests must never depend on or spend a real AI provider call: force both
# providers "unconfigured" regardless of what's in backend/.env.
os.environ["GEMINI_API_KEY"] = ""
os.environ["ANTHROPIC_API_KEY"] = ""

import pymongo
import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app


@pytest.fixture()
def client():
    settings = get_settings()
    with TestClient(app) as test_client:
        yield test_client
    # Sync client for teardown: the async motor client's event loop is
    # already closed by the time TestClient's lifespan context exits.
    pymongo.MongoClient(settings.mongodb_uri).drop_database(settings.mongodb_database)
