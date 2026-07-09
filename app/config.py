"""Application configuration.

Two distinct things live here:

* :class:`Config` / :class:`TestConfig` — Flask config objects consumed by the
  application factory (SECRET_KEY, server bind host/port).
* ``config`` — the runtime, user-mutable settings dict (interface / wordlist /
  output_dir). It is kept as a module-level mutable dict because the Settings UI
  mutates it live (``config['interface'] = ...``), exactly as the old
  ``web.shared.config`` did.

Values are hardcoded to the original defaults to keep the restructure strictly
behavior-preserving. The only sanctioned config-behavior change is SECRET_KEY, which the
factory reads from ``AIRSTRIKE_SECRET_KEY`` (falling back to a generated key with a
warning). Making the rest env-driven would be an easy, separate follow-up.
"""


# Runtime, user-mutable settings (was web.shared.config).
config = {
    "interface": "wlan0",
    "wordlist": "/usr/share/wordlists/rockyou.txt",
    "output_dir": "./captures/",
}


class Config:
    """Base Flask configuration.

    SECRET_KEY is intentionally left unset here; the factory resolves it from
    ``AIRSTRIKE_SECRET_KEY`` or generates an ephemeral one with a warning.
    """

    DEBUG = False
    HOST = "0.0.0.0"
    PORT = 5000


class TestConfig(Config):
    """Configuration for the test suite: no root, no real secret, testing on."""

    TESTING = True
    SECRET_KEY = "test-secret-key"
