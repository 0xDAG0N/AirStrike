"""Thin service layer: orchestration logic pulled out of the blueprints.

Only the features with real orchestration have a service module (attacks, scan, settings).
Trivial features (main, diagnostics, results) keep their logic inline in their blueprint —
manufacturing empty service files for them would be ceremony, not structure.
"""
