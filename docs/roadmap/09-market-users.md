# 09 — Market & Target Users

**Objective:** aim at the one audience that's actually reachable and additive.
**Current → Target:** D (3/10) → C (5/10)
**Why it matters:** the professional pentest audience is blocked by design (unauth root
control, fewer features, they'll use Kali over SSH). The realistic audience is **learners** —
and that audience is served by content + packaging, not by out-featuring incumbents.

## Target segments (in priority order)
1. **Security students / people learning 802.11 attacks** — primary. They value clarity and
   safe defaults over raw power.
2. **CTF players & home-labbers** — want a fast, visual, isolated-lab tool.
3. **Educators** — could use it as a teaching aid / assignment.
4. ~~Professional red teams~~ — *not* a realistic target; don't design for them.

## Workstreams

### M1 — Package for the learning audience
- Ship a **Docker-based lab** (isolated network) so an unauthenticated-panel-in-a-VM is
  acceptable and the teaching value is highest (pairs with 03/F5, 06, 07).
- A "quickstart in 5 minutes" path; sample targets in a contained lab.
- Consider a **TryHackMe / HTB-style companion room** or guided exercises.

### M2 — Build the reputation funnel (this is the real growth engine)
- Publish companion write-ups/videos: "how deauth frames work," "capturing the 4-way
  handshake," "evil-twin DHCP/DNS spoofing." Each links back to AirStrike as the visual
  companion.
- These double as **portfolio proof of understanding** — the assessment's #1 recommended
  reputation move. Top-of-funnel for learners + credibility for hiring.

### M3 — Honest positioning to the segment
- The README/site speak to learners ("understand these attacks in a safe lab"), not to
  "the industry." Overclaiming repels the very reviewers whose respect is the payoff (10).

## Effort
M1: ~2–3 days. M2: ongoing content (the highest-ROI ongoing activity).

## Dependencies
Downstream of 06 (identity) + 01/07 (must be safe/lab-framed first). M2 content can start
early — it's mostly explanatory.

## Definition of done
- A one-command Docker lab; a "start here" path for a student.
- At least a first companion write-up/video published and linked.
- Messaging targets learners, not enterprises.
