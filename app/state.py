"""Runtime coordination state shared between request handlers and worker threads.

This was the mutable-global heart of the old ``web.shared`` module. It is now a single,
named home with a ``threading.Lock`` guarding the compound mutations (log append, reset,
and the attack check-and-set in :mod:`app.services.attack_service`).

The single-attack / single-process model is unchanged — ``attack_state`` is a dict plus a
lock, not a scheduler. Turning this into a multi-attack manager is deliberately out of
scope for the structural refactor.
"""

import time
import threading

from app.core.logging import logger

# Guards the compound mutations of the dicts below. Critical sections are kept tiny and
# never held across I/O or thread joins, so there is no deadlock risk.
state_lock = threading.Lock()

# Attack coordination bus.
attack_state = {
    "running": False,
    "attack_type": None,
    "target_network": None,
    "progress": 0,
    "log": [],
    "stop_event": None,
    "threads": [],
}

# Dashboard statistics.
stats = {
    "networks_count": 0,
    "attacks_count": 0,
    "captures_count": 0,
}

# Initialize stop event.
attack_state["stop_event"] = threading.Event()


def log_message(message):
    """
    Append a message to the attack log and the application logger.

    This is the state-aware log sink (append + logger, no socket emit) that the old
    ``web.shared.log_message`` / ``add_log_message_shared`` provided, and it is the
    callback injected into the engine workers.
    """
    timestamp = time.strftime("%H:%M:%S")
    formatted_message = f"[{timestamp}] {message}"
    with state_lock:
        attack_state["log"].append(formatted_message)
    logger.info(formatted_message)


def reset_attack_state():
    """
    Reset the attack state to default values.
    This should be called when an attack is stopped or fails.
    """
    with state_lock:
        attack_state["running"] = False
        attack_state["attack_type"] = None
        attack_state["progress"] = 0

        # Properly clean up threads and events
        if attack_state["stop_event"] and not attack_state["stop_event"].is_set():
            attack_state["stop_event"].set()

        # Create a new event for future attacks
        attack_state["stop_event"] = threading.Event()
        attack_state["threads"] = []
