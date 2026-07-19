# Design decision 0001 — Win condition: literal / visible-only

- **Status:** Accepted
- **Date:** 2026-07-19
- **Context tags:** rules-interpretation, engine

## Context

The brief states: *"a player wins when their hand is empty and, among their
visible poles, only pole 3 has disks on it."* A player's visible poles are
`pole1`, the shared `pole2`, and `pole3`.

Because either player can lift from the shared pole and place onto their own
hidden poles, a disk can be **stranded** on the opponent's side, unreachable
forever. This creates an ambiguity: does "only pole 3 has disks" mean

- **(Literal)** merely that `pole1` and `pole2` are empty and `pole3` is
  non-empty — regardless of how many disks reached `pole3`; or
- **(Strict)** that *all N* of the player's disks are stacked on `pole3`?

## Decision

Adopt the **literal / visible-only** reading:

```
win(P) ⇔ hand(P) is empty
       ∧ pole1(P) is empty
       ∧ SHARED    is empty
       ∧ pole3(P) is non-empty
```

The engine tracks **no** disk ownership and performs **no** disk count for the
win check.

## Consequences

- **Simpler, smaller core.** No ownership metadata threaded through state; the
  check reads four visible facts.
- **Still forces real solving.** To empty `pole1` and `SHARED`, a player must
  move essentially all their disks to `pole3` (or lose them to stranding);
  the literal rule does not create cheap wins in practice.
- **Faithful to wording.** Matches the spec's exact phrasing; the strict
  reading adds requirements the text does not state.
- **Stranding is a real losing risk,** not an engine error: a player who lets
  disks be stranded may be unable to satisfy the condition at all. That is
  gameplay, not a bug.

## Alternatives considered

- **Strict (all N on pole3):** requires ownership tracking and a count; makes
  some positions permanently unwinnable in a way the text does not demand.
  Rejected as heavier and less faithful.
