"""Framework-agnostic shared plumbing (logging, sudo/system helpers, network utils).

Nothing in this package may import Flask, Flask-SocketIO, or any ``app.blueprints`` /
``app.sockets`` / ``app.services`` module. It is the bottom layer of the import graph.
"""
