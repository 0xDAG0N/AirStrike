"""Wireless-attack engine (deauth flood, WPA-handshake capture/crack, evil-twin AP).

This package is framework-agnostic: it MUST NOT import Flask, Flask-SocketIO, or any
``app.blueprints`` / ``app.sockets`` / ``app.state`` module. Worker functions receive a
``log`` callback (and ``stop_signal``) as parameters instead of importing the web layer,
so the engine is importable and unit-testable with Flask absent.
"""
