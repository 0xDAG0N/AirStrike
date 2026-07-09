# 08 — Competitive Positioning

**Objective:** stop competing where you lose; compete where incumbents are weak.
**Current → Target:** D (3/10) → C+ (6/10)
**Why it matters:** AirStrike is a strict feature-subset of free tools and a hobby subset of
the commercial one. You will not out-feature wifite2/airgeddon on attack breadth, and you
won't out-hardware Hak5. The grade rises only by *changing the axis of competition*.

## The landscape (2026)

| | Attacks | WPA3 | GPU crack | UI | Cost |
|---|---|---|---|---|---|
| **AirStrike** | 3 (deauth, handshake, evil-twin) | blind | CPU only | **web + teaching** | free |
| wifite2 | PMKID, WPS, handshake | no | hashcat | CLI | free |
| airgeddon | + captive portal, WPA3 dict | partial | yes | menu/TUI | free |
| bettercap | PMKID, rogue AP, MITM | no | no | CLI+web | free |
| WiFi Pineapple | broad | partial | partial | polished web | $120–850 |

## Workstreams

### C1 — Win on the education axis (pairs with 06 Option A)
- Nobody in the list optimizes for *learning*. Make "clearest, safest way to understand these
  attacks" the competitive claim. This is a defensible niche incumbents ignore.

### C2 — Win on ergonomics/orchestration, not attack count (pairs with 06 Option B)
- Incumbents' real weakness is bash/CLI ergonomics and no reporting. If pursuing the operator
  path: multi-target campaigns, structured **engagement reports / evidence export**, guided
  workflows, team features — the layer above the tools.

### C3 — Close only the gaps that keep you honest
- Don't chase parity. But **WPA3/PMF detection** (05/D3) is mandatory — a tool that silently
  runs a deauth that PMF blocks looks broken/dishonest. PMKID + hashcat are optional
  "credibility" adds if going the operator route.

### C4 — Honest comparison in the README
- Publish a candid comparison table (like above). Owning your limitations reads as maturity to
  the audience that matters (reviewers, learners) — far better than "most advanced ever."

## Effort
Positioning + honest comparison: ~1 day. Feature parity (C3 beyond PMF detection): weeks
(only if 06 Option B).

## Dependencies
Downstream of 06 (identity decides which axis). C4 pairs with 04/T4 README work.

## Definition of done
- README states the competitive axis (education *or* orchestration) and an honest comparison.
- WPA3/PMF detection shipped so the tool never runs an attack it knows will fail.
