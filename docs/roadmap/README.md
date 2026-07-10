# AirStrike Enhancement Roadmap

> Master plan. Derived from the July 2026 independent assessment (overall **C− / 4.0**).
> Each perspective has its own sub-plan in this folder.

## The strategic decision that drives everything

AirStrike cannot win as a *product* — it's a strict feature-subset of free incumbents
(wifite2, airgeddon, bettercap) and its browser-UI angle is already owned by Hak5's WiFi
Pineapple. Its real, realizable value is **engineering credibility** (portfolio) and, if
extended, a **teaching tool** — the one axis where a web UI genuinely beats a bare CLI.

So the north star is: **make AirStrike the artifact that gets its author hired, and
optionally the clearest on-ramp for learning 802.11 attacks.** Every enhancement is judged
against that, not against revenue.

Two non-negotiables fall out of this:
1. **Security first.** A "security tool" with unauthenticated remote root RCE actively
   *destroys* credibility. This is the gate — nothing ships publicly until it's closed.
2. **Honesty first.** The "most advanced Wi-Fi tool. Ever." marketing is the single
   biggest threat to the portfolio value. Reframe to match reality.

## Phasing

| Phase | Theme | Goal | Perspectives |
|---|---|---|---|
| **P0 — Stop the bleeding** | Security + honesty | Make it safe & honestly framed enough to show anyone | 01 Security, 07 Legal/Ethical, 06 (reframe only) |
| **P1 — Earn the grade** | Credibility & finish | Turn it into a portfolio A-piece | 02 Architecture, 03 Frontend, 04 Testing/CI, 05 Stack |
| **P2 — Earn a reason to exist** | Differentiation | Pick the education/orchestration niche & build the one thing a UI does better | 06 Idea, 08 Competitive |
| **P3 — Optional: reach** | Audience & (maybe) money | Grow reputation; decide if any product ambition is worth it | 09 Market, 10 Monetization |

**Do the phases in order.** P0 unblocks public promotion; P1 makes the code back the story;
P2 gives it a defensible identity; P3 is optional and only worth it after P0–P1.

## Dependency graph (what blocks what)

```
01 Security ──┬─→ 07 Legal (auth gate + audit log build on the security work)
              └─→ everything public-facing (nothing ships until this lands)
04 Testing/CI ──→ safety net for 02 Architecture + 05 Stack changes
05 Stack (fix pins) ──→ 04 clean-install smoke test can pass
06 Idea (pick identity) ──→ 08 Competitive + 03 Frontend (what to build the UI around)
02/03/04/05 (P1 finish) ──→ 09/10 (no point marketing an unfinished tool)
```

## Success metrics

- **Security:** 0 `shell=True` / `os.popen`; auth required; bound to loopback; a clean
  `pip install` + `pytest` + `ruff` green in CI; a published threat model.
- **Portfolio:** README leads with architecture + the before/after refactor story + a
  candid limitations section; no overclaiming.
- **Identity:** one sentence anyone can repeat about what AirStrike is *for*.
- **Reach (optional):** GitHub stars from learners; a companion write-up/video series.

## The sub-plans

**Technical**
- [01 — Security](01-security.md) · D(2) → target B(7)  *(highest priority)*
- [02 — Architecture & code quality](02-architecture.md) · C−(4) → A−(8)
- [03 — Frontend & UX](03-frontend-ux.md) · C(5) → B+(8)
- [04 — Testing, CI & packaging](04-testing-ci-packaging.md) · B−(6) → A(9)
- [05 — Technology & stack](05-tech-stack.md) · B(7) → A−(8)

**Business**
- [06 — Idea & differentiation](06-idea-differentiation.md) · C(4) → B(7)
- [07 — Legal, ethical & compliance](07-legal-ethical.md) · D(4) → B+(8)
- [08 — Competitive positioning](08-competitive.md) · D(3) → C+(6)
- [09 — Market & target users](09-market-users.md) · D(3) → C(5)
- [10 — Product, monetization & GTM](10-product-monetization.md) · D(3) → *reframe*

## How to read a sub-plan

Each one has: **Objective**, **Current → Target**, **Why it matters**, **Workstreams**
(prioritized, concrete tasks with file references), **Effort**, **Dependencies**, and a
**Definition of done**.
