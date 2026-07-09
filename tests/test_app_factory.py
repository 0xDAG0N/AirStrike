"""Factory + route-contract tests.

The frontend hardcodes every backend URL, so the set of registered routes IS a contract.
These tests fail loudly if a route goes missing or the old ``/attack_status`` /
``/attack_log`` collision comes back.
"""

from collections import Counter

# Every URL the frontend depends on. Byte-identical to the pre-refactor route set.
EXPECTED_ROUTES = {
    "/",
    "/dashboard_stats",
    "/scan",
    "/scan_wifi",
    "/attack",
    "/start_attack",
    "/stop_attack",
    "/settings",
    "/get_interfaces",
    "/set_interface",
    "/save_wordlist",
    "/save_output_dir",
    "/results",
    "/attack_status",
    "/attack_log",
    "/captured_handshakes",
    "/diagnostics",
    "/run_diagnostic",
    "/check_permissions",
    "/test_deauth",
}


def test_factory_builds(app):
    assert app is not None
    assert app.config["TESTING"] is True
    assert app.config["SECRET_KEY"]


def test_all_contract_routes_registered(app):
    rules = {r.rule for r in app.url_map.iter_rules()}
    missing = EXPECTED_ROUTES - rules
    assert not missing, f"missing contract routes: {sorted(missing)}"


def test_no_duplicate_route_rules(app):
    rules = [r.rule for r in app.url_map.iter_rules() if r.endpoint != "static"]
    dupes = [rule for rule, n in Counter(rules).items() if n > 1]
    assert not dupes, f"duplicate route rules (collision regression): {dupes}"


def test_attack_status_and_log_owned_by_results(app):
    endpoints = {r.rule: r.endpoint for r in app.url_map.iter_rules()}
    # The old code declared these in BOTH attacks_bp and results_bp; results must be sole owner.
    assert endpoints["/attack_status"] == "results.attack_status"
    assert endpoints["/attack_log"] == "results.attack_log"


def test_index_serves(client):
    resp = client.get("/")
    assert resp.status_code == 200
