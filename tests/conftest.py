"""Shared pytest fixtures.

The application factory has no root requirement (root enforcement lives in ``app.cli``),
so tests build the app directly with ``TestConfig`` — no sudo, no wireless hardware.
"""

import os

import pytest

# Belt-and-suspenders in case any code path consults this.
os.environ.setdefault("AIRSTRIKE_SKIP_ROOT_CHECK", "1")

from app import create_app
from app.config import TestConfig


@pytest.fixture
def app():
    application = create_app(TestConfig)
    application.config.update(TESTING=True)
    return application


@pytest.fixture
def client(app):
    return app.test_client()
