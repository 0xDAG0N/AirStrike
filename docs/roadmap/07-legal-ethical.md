# 07 — Legal, Ethical & Compliance

**Objective:** move from cosmetic disclaimers to enforced, responsible guardrails.
**Current → Target:** D (4/10) → B+ (8/10)
**Why it matters:** AirStrike ships actively-illegal-without-authorization, FCC-regulated
attacks (deauth is FCC §333; evil-twin/CFAA/UK CMA s.3A/StGB §202c exposure). The disclaimers
exist and are decently worded but **gate nothing**. For a portfolio, *demonstrating* mature
handling of dual-use risk is itself a strong signal.

## Workstreams

### L1 — Enforce authorization (not just warn)
- **Consent/scope gate on startup and per-engagement:** the operator explicitly confirms they
  are authorized and enters an in-scope target set (BSSID/ESSID allow-list). Attacks refuse
  targets outside the confirmed scope.
- **Audit log** (shared with 01/S6): every attack records operator, target, timestamp, action —
  a real accountability trail.

### L2 — Lab-only default posture
- Default to loopback bind + an isolated-lab framing (pairs with 06 Option A and 03 Docker
  lab). "For authorized testing and education on networks you own" is the *default*, not a
  footnote.

### L3 — Honest, load-bearing disclaimers
- Replace boilerplate with a clear **usage policy** + a `THREAT_MODEL.md` / limitations
  section that names the tool's own risks (the security findings) — turning weakness into
  evidence of maturity.
- Add explicit legal notices to the README and first-run screen; reference the relevant
  statutes so users understand the stakes.

### L4 — Responsible distribution
- Review the LICENSE for an acceptable-use clause. Consider whether the aggressive public
  marketing channel (custom domain, "industry standard") is consistent with responsible release
  — reframe to education (ties to 10).
- Add a `SECURITY.md` with a responsible-disclosure contact.

## Effort
~2–3 days (L1 is the real work; the rest is writing + config).

## Dependencies
Builds directly on 01 (auth + audit log). Reframing pairs with 06/10.

## Definition of done
- No attack runs without an explicit authorization confirmation + an in-scope target.
- Audit log present; `THREAT_MODEL.md`, usage policy, and `SECURITY.md` published.
- Marketing/README framing is education-first and legally honest.
