# 06 — Idea & Differentiation

**Objective:** give AirStrike one defensible identity instead of being a worse copy of
everything.
**Current → Target:** C (4/10) → B (7/10)
**Why it matters:** "a web dashboard for three WiFi attacks" is moat-less — free `airgeddon`
does more with a menu, and Hak5 owns the polished-UI pitch with hardware. But there is one
lane the incumbents are weak in.

## The positioning decision

Pick **one** and commit:

### Option A (recommended) — Educational lab visualizer
Reframe AirStrike as *the clearest way to learn 802.11 attacks*. The web UI earns its
existence by **teaching**, which a CLI can't:
- Inline, step-by-step explanations of each attack (what a deauth frame is, the 4-way
  handshake, evil-twin DHCP/DNS spoofing).
- **Live visualization** — packets, the handshake capture, channel/AP state — as it happens.
- Safe-by-default, lab-only framing (pairs with 07). Ships as a Docker lab against an isolated
  network.
- Audience: students, CTF players, home-labbers (see 09). This is where a beginner's teaching
  instinct is a *strength*, not a liability.

### Option B — Orchestration layer for real operators
Differentiate on what headless CLIs lack: **multi-target campaigns, structured engagement
reporting / evidence export, guided scan→attack workflows, scope/consent gating.** Become the
*workflow* around the tools, not a button that runs `airodump`. Higher bar (requires the
security + legal work to be airtight, and credibility you don't have yet).

**Recommendation:** A now (it's reachable and plays to strengths), keep B as the long-term
stretch if the tool proves out.

## Workstreams
- Write a **one-sentence identity** and put it at the top of the README + site (replaces the
  overclaiming — see 07/10).
- Scope the teaching features (06 ↔ 03/F6): pick the 2–3 highest-value visualizations.
- Add **WPA3/PMF awareness** (05/D3): honestly show *when* an attack applies — a teaching tool
  must not lie about a declining attack surface.
- Companion content plan (feeds 09): each attack gets a "how it works" write-up/video.

## Effort
Positioning: hours. The teaching UI: the main P2 feature investment (weeks).

## Dependencies
Drives 03 (what the UI is built around) and 08 (how it competes). Blocked only by needing
01/07 done first (can't market a teaching-safe tool that's unsafe).

## Definition of done
- One sentence, everywhere, that says what AirStrike is *for*.
- At least one teaching visualization shipped that a CLI genuinely can't match.
