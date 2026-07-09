# 10 — Product, Monetization & GTM

**Objective:** be honest that the ROI here is *career capital*, not revenue — and optimize for
that.
**Current → Target:** D (3/10) → *reframed* (the goal isn't a higher "product" score; it's
maximizing the real payoff).
**Why it matters:** three independent walls block productization — no moat, no monetization
path (the category monetizes via **hardware + services**, not software; hosted SaaS is
physically impossible because attacks need local RF), and legal radioactivity. Chasing
"product" is negative expected value. The value is real, just not commercial.

## What NOT to do
- ❌ **Hosted SaaS** — impossible (local RF hardware required) and forbidden by cloud AUPs.
- ❌ **Hardware appliance** — walks straight into Hak5/Flipper on their turf; capital-intensive,
  no edge.
- ❌ **Paid license** — nobody pays for a subset of free, Kali-shipped tools.

## The reframe: optimize for credibility
The realistic "business model" is **employability + reputation**. Concretely:

### G1 — Turn the repo into an A-grade portfolio artifact  *(the main GTM)*
- Lead the README with: the architecture + the **before/after refactor story** (02/A4), a
  candid **limitations/threat-model** section (01/07), and the honest competitive framing (08).
- Retire "the most advanced Wi-Fi tool. Ever. / the industry standard / a platform." This
  overclaiming is the **single biggest threat** to the one asset that pays off — credibility
  with senior reviewers. This change costs nothing and is the highest-ROI move on the list.

### G2 — Reputation funnel (shared with 09/M2)
- Companion write-ups/videos → GitHub stars from learners → demonstrable public evidence of
  skill. Success metric: stars/engagement from the learning community, cited in a CV/portfolio.

### G3 — Optional, only if there's genuine pull
- **OSS-core + courseware/training** is the one semi-viable money-adjacent path (teach the
  attacks, tool is the lab) — but treat it as a content business, not a software one.
- **Consulting lead-gen** requires a real credential (OSCP / CPTS / PNPT) to be credible — the
  tool alone won't generate leads. Pursue the cert first if this is the ambition.

## Effort
G1: ~1 day (highest ROI on the entire roadmap). G2: ongoing. G3: optional, months.

## Dependencies
G1 depends on 01/02/04/07 being far enough along that the code backs the story. Do it **last**
in P1 / early P3 — after the tool is safe and finished enough to withstand scrutiny.

## Definition of done
- README/site reframed: honest, education-first, no overclaiming.
- A clear, repeatable one-line pitch of what AirStrike is and who it's for.
- A decision recorded on G3 (pursue courseware/consulting or explicitly not).
