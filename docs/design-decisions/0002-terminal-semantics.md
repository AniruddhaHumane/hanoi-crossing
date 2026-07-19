# Design decision 0002 — Terminal semantics: check both players, freeze on first win

- **Status:** Accepted
- **Date:** 2026-07-19
- **Context tags:** rules-interpretation, engine

## Context

The win condition (see decision `0001`) is a **local property of a player's visible
poles**. A move by one player can therefore complete the *other* player's win:
if A has all disks on `pole3`, hand empty, `pole1` empty, but one stray A-disk
remains on the shared pole, then when **B** lifts that disk off the shared pole,
A's win condition becomes satisfied on **B's** turn.

Two questions follow:

1. After a step, **whose** win do we evaluate?
2. Once someone has won, what happens to **subsequent** moves?

## Decision

1. **Check both players after every step.** The engine evaluates `is_win` for
   both A and B on each transition, not only for the player who just moved.
2. **Freeze on first win.** The first player found winning ends the game; the
   resulting state carries `terminal = True` and a `winner`. Subsequent `step`
   calls on a terminal state are **no-ops** (state returned unchanged).
3. **Tie-break:** if a single move satisfies the win condition for *both*
   players simultaneously, the **player who just moved** wins. This is a fixed,
   deterministic rule so replays are reproducible.
4. `is_win(state, player)` is exposed as a **public pure query** and reused
   internally to set the terminal flag — a single source of truth.

## Consequences

- **Correct per the local win rule.** A win caused by the opponent's move is
  detected immediately, not deferred to the winner's next turn.
- **One unambiguous end signal** for every consumer (replay, random-play,
  future RL loop, sim service) — terminal bookkeeping lives in the engine, not
  duplicated in each driver.
- **Reproducible.** The deterministic tie-break removes any ambiguity from
  simultaneous completion.

## Alternatives considered

- **Check only the acting player:** simpler loop, but silently violates the
  local win rule (misses the "opponent completes your win" case until your next
  turn, or forever if the turn order never returns to you). Rejected.
- **Never freeze; engine only offers `is_win`:** smallest core, but pushes
  terminal bookkeeping into every consumer and de-standardizes when a game
  ends. Rejected — though the public `is_win` query from this option is kept.
