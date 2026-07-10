"""Shared pytest fixtures.

The application factory now installs a login gate + CSRF guard, so tests use an
already-authenticated client (session seeded with a known CSRF token) plus an
``anon_client`` for exercising the gate itself.
"""

import os

import pytest

# Deterministic auth for the suite; must be set before create_app() reads it.
os.environ.setdefault("AIRSTRIKE_SKIP_ROOT_CHECK", "1")
os.environ.setdefault("AIRSTRIKE_PASSWORD", "test-pass")
# Auth is off by default now (loopback); force it on so the auth/CSRF suite exercises the gate.
os.environ.setdefault("AIRSTRIKE_REQUIRE_AUTH", "1")

from app import create_app
from app.config import TestConfig

TEST_CSRF = "test-csrf-token"


@pytest.fixture
def app():
    application = create_app(TestConfig)
    application.config.update(TESTING=True)
    return application


@pytest.fixture
def client(app):
    """Authenticated client with a known CSRF token seeded into the session."""
    c = app.test_client()
    with c.session_transaction() as sess:
        sess["authenticated"] = True
        sess["csrf_token"] = TEST_CSRF
    return c


@pytest.fixture
def csrf():
    """The CSRF token seeded into the authenticated ``client``."""
    return TEST_CSRF


@pytest.fixture
def anon_client(app):
    """Unauthenticated client, for testing the login gate."""
    return app.test_client()
