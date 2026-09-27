# Debt triage — `tk appappearance` fallback and plain-tk default backgrounds

Date: 2026-09-27. Scope: two items in the Known Architectural Debt list of `DESIGN.md`.

## Decision 1 — keep the `tk appappearance` attempt (former debt item 2)

The clam+palette fallback path is what is always live on this machine (Tcl/Tk 9.0.4
rejects `tk appappearance` with `TclError`). The guarded native attempt is kept rather
than deleted because:

- It is a one-call probe behind `try/except TclError`; it costs nothing and cannot
  break the fallback path.
- If the Tk runtime is ever upgraded to a build that supports native appearance,
  theming improves with zero code change.
- Removing it would trade a harmless probe for a permanent dependency on the
  manual-palette behavior in every environment.

Accepted as-is. It is documented as environment behavior in `DESIGN.md` →
External Interfaces (Tk/Tcl quirks), not as debt.

## Decision 2 — plain-tk default `-bg` pinning is a constraint, not debt (former debt item 3)

Plain `tk` widgets resolve their default `-bg` to `systemWindowBackgroundColor` once
at creation. This is an immutable property of the widget toolkit, not of our code.
The `self._palette` mechanism (explicit per-widget backgrounds, re-applied on theme
toggle via `_refresh_items`) is the established mitigation and is complete for the
current UI. Revisiting this would mean migrating to ttk-only widgets, a large
regression-risk change with no user-visible benefit.

Accepted as a standing constraint. Action rule for future UI work: any new plain-tk
widget must take its background from `self._palette` and be covered by
`_refresh_items`.