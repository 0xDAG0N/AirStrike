# 03 — Frontend & UX

**Objective:** make the UI honest, safe, accessible, and actually better than a CLI.
**Current → Target:** C (5/10) → B+ (8/10)
**Why it matters:** the web UI is AirStrike's *only* differentiator. Right now it's
undercut by security holes and "theatre" code that a reviewer reads as cargo-culting.

## Workstreams

### F1 — Fix the XSS  *(blocker — shared with 01/S4)*
- Add `escapeHtml()`; replace all 21 unescaped `innerHTML` sinks with escaped insertion or
  `textContent`. Applies to network lists, network info, and the live log.

### F2 — Delete the dead theatre
- Remove the never-subscribed Redux-style `subscribe()/notifySubscribers()` in `state.js`
  (state is read imperatively) and the second, manually-synced `sessionStorage` store —
  pick one source of truth.
- Remove `initializeUI()/setupThemeToggle()/setupAlerts()` in `main.js` that are never called.
- Fix the fake progress bar in `page-transitions.js` (5 steps all say "Loading resources…"
  over ~60ms) — either show real progress or delete it.
- Fix the "SPA" in `navigation.js`: it `preventDefault()`s then does
  `window.location.href = targetUrl` (a full reload it would've done anyway) and the popstate
  handler self-reassigns. Either commit to real client-side routing or remove the interception.

### F3 — Fix the silent-failure bug
- `main.js` `catch (error)` **shadows** the imported `error` toast function, so init failures
  throw a `TypeError` and are swallowed. Rename the caught variable (`catch (err)`).

### F4 — Accessibility
- Give the live log an `aria-live="polite"` region (it's the primary realtime surface).
- Make network rows real controls: `role`/`tabindex`/keyboard handlers (currently mouse-only
  clickable `<div>`s).
- Replace the blocking `window.alert()` for cracked passwords with the existing toast system.
- Add focus-visible states; audit the ~6 aria/role/label usages upward.

### F5 — Offline/air-gapped robustness
- **Vendor `socket.io` and Google Fonts locally.** On the air-gapped Kali boxes where this
  runs, the CDN `socket.io` fails to load → the marquee live-log feature dies.
- Remove `DEBUG=true` and stray `console.log`s.
- Add real responsive breakpoints (only ~3 media queries today; nav row breaks on mobile).

### F6 — Earn the UI's existence (ties to 06)
- The UI should *teach*: inline explanations of each attack step, a live 4-way-handshake /
  packet visualization, safe defaults. This is the one thing a CLI can't do well.

## Effort
~3–4 days (F1–F3 are ~1 day and high-value; F6 is the ambitious, differentiating part).

## Dependencies
F1 is part of the 01 security gate. F6 depends on 06 (identity).

## Definition of done
- No unescaped attacker data in the DOM; no dead/never-called frontend code.
- Live log works fully offline; keyboard-navigable; `console` clean.
- (Stretch) at least one genuine attack visualization that a CLI cannot match.
