# Development log

A concise record of the journey: decisions, insights, and what tripped me up.
Detailed rationale for the two biggest calls lives in `docs/design-decisions/`.

## Approach

Design-first, then test-first per module. Build order followed the dependency
graph: `state → actions → observation → rules → frontends`, each written as a
failing test suite before the implementation. Every slice went through its own
branch, PR, and CI run.

## Key decisions and why

- **Win = literal / visible-only** (`design-decisions/0001`). The win is a pure
  property of a player's visible poles (`hand empty ∧ pole1 empty ∧ SHARED empty
  ∧ pole3 non-empty`). Tracking disk ownership added complexity the brief didn't
  ask for, and the literal rule still forces a real solve — you can't clear
  pole 1 and the shared pole without moving your disks to pole 3 (or losing
  them).
- **Player-relative pole addressing.** Each player only ever names `pole 1/2/3`
  (pole 2 = shared). The engine maps `(player, local) → physical`. This makes
  hidden information *structural*: a player literally cannot name the opponent's
  poles, and both players share one symmetric 7-action space — ideal for
  self-play RL later.
- **Pure, immutable core behind an observation boundary.** `step` is a pure
  function returning a new state; agents receive only an `Observation`. This is
  the single design choice that lets the engine double as an RL env or a
  concurrent sim with no changes.

## Insights and gotchas

- **Globally-unique disk sizes remove all ties.** A owns odds, B owns evens, so
  any two disks — even across players on the shared pole — have a strict order.
  The Hanoi placement rule is therefore always well-defined; no tie-breaking on
  equal sizes is ever needed.
- **Frozen ≠ deeply immutable.** My first `GameState` stored poles in a `dict`.
  A frozen pydantic model blocks attribute *reassignment* but not in-place dict
  *mutation* (`state.poles[p] = ...` still worked). I switched to per-pole tuple
  fields (`a1, a3, b1, b3, shared`) plus hand fields, making the state genuinely
  immutable with no extra machinery.
- **A win can be triggered by the opponent.** Because the win is local to
  visible poles, one player's move can complete the other's win (e.g. B lifting
  a stray disk off the shared pole clears it and wins for A). So the engine
  checks *both* players after every step, not just the mover.
- **An empty board is not a win.** If a player's disks get stranded on the
  hidden side and pole 3 ends empty, the "pole 3 non-empty" clause correctly
  reports *no win* — that's a lost position, not a victory.
- **The simultaneous-win tie is unreachable.** Completing a win needs the shared
  pole empty *and* an empty hand; a single move can't leave both players newly
  satisfying that. I encode the "actor wins ties" rule implicitly by checking
  the actor first, avoiding an untestable branch.

## Challenges

- **Test-first vs a pytest pre-commit gate.** A pre-commit hook that runs the
  tests will reject the intentionally-failing "RED" commit of a test-first flow.
  Resolved by scoping pre-commit to fast checks (ruff + hygiene) and running the
  test suite in CI — the standard split — which also lets the git history show a
  clean green → red → green per feature.
- **CI required-check naming.** Branch protection required a check named `Lint`
  while the job reported as `Lint (ruff)`; the mismatch silently blocked merges
  until the job was renamed.

## Performance & limitations (honest)

- **Per-step allocation cost.** Replaying 1,000,000 moves took ~13.6 s and
  ~1.1 GB peak RSS, because each `step` builds a fresh immutable state and
  pydantic validates on construction. For a hot RL loop this is the thing to
  optimise first — `model_construct`/`model_copy` skip re-validation on the
  trusted path; a further step would be lighter-weight state objects.
- **No cap on N.** `initial_state` validates `n ≥ 1` but not an upper bound, so a
  pathologically large N (e.g. 10⁸) will exhaust memory. A real service would
  bound N at the boundary.

## Testing

91 tests, ~96% coverage: engine units (setup, mapping, accessors, legality,
immutability, win detection, terminal freeze, the spec N=1 game), plus frontend
tests for the DSL parser, the random player (determinism, only-legal moves), and
both CLI commands.
