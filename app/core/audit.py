"""Audit logging for accountability (P0 · S6, docs/roadmap/01-security.md).

Every attack launch/stop is recorded as a JSON line — who (session), what (attack type +
target), when, and the operator's explicit authorization confirmation. This turns the
"disclaimers gate nothing" gap into an enforced, reviewable record.
"""

import os
import json
import time

from app.core.logging import logger

# Best-effort append-only audit trail; override the location with AIRSTRIKE_AUDIT_LOG.
_AUDIT_PATH = os.environ.get("AIRSTRIKE_AUDIT_LOG", "airstrike-audit.log")


def audit(event, **fields):
    """Record an audit event to the log stream and the audit file (never raises)."""
    entry = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "event": event, **fields}
    line = json.dumps(entry, ensure_ascii=False)
    logger.info("AUDIT %s", line)
    try:
        with open(_AUDIT_PATH, "a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    except OSError as exc:
        logger.error("audit write failed (%s): %s", _AUDIT_PATH, exc)
