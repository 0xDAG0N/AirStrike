"""Pure-function tests for the capture engine.

These functions were previously impossible to import without Flask (the engine imported
``web.shared``). They are now directly importable — this test file is proof of the
decoupling as much as it is a unit test.
"""

from app.engine.capture_attack import parse_aircrack_password, has_full_wpa_handshake


def test_parse_aircrack_password_found():
    assert parse_aircrack_password("stuff\nKEY FOUND! [ hunter2 ]\nmore") == "hunter2"


def test_parse_aircrack_password_strips_ansi():
    raw = "\x1b[2K\x1b[1;32mKEY FOUND! [ p@ss ]\x1b[0m"
    assert parse_aircrack_password(raw) == "p@ss"


def test_parse_aircrack_password_none():
    assert parse_aircrack_password("no key in here") is None
    assert parse_aircrack_password("") is None
    assert parse_aircrack_password(None) is None


def test_full_handshake_detected():
    out = "Message 1 of 4\nMessage 2 of 4\nMessage 3 of 4\nMessage 4 of 4"
    complete, seen = has_full_wpa_handshake(out)
    assert complete is True
    assert seen == {1, 2, 3, 4}


def test_partial_handshake_not_detected():
    complete, seen = has_full_wpa_handshake("Message 1 of 4\nMessage 2 of 4")
    assert complete is False
    assert seen == {1, 2}


def test_empty_handshake_input():
    complete, seen = has_full_wpa_handshake("")
    assert complete is False
    assert seen == set()
