# Development log

Rough notes on how this went: the decisions, the things I got wrong first, and
what I'd still improve. The two big rule calls have their own write-ups in
`docs/design-decisions/`.

## How I built it

Design first, then one module at a time in dependency order: state, actions,
observation, rules, then the frontends. Tests came before each implementation,
and each piece went on its own branch through a PR and CI.

## Decisions

Win condition. I made it literal and visible-only (hand empty, pole 1 empty,
shared empty, pole 3 non-empty). Tracking who owns which disk was more machinery
than the brief needed, and the literal rule still forces a real solve: you can't
clear pole 1 and the shared pole without getting your disks onto pole 3 (or
losing them).

Player-relative poles. Each player only names pole 1/2/3 and the engine maps that
to the physical pole. This makes hidden information structural instead of a check
I have to remember: a player can't even refer to the opponent's poles, and both
players get the same 7-action space, which is handy for self-play later.

Pure, immutable core. `step` returns a new state and agents only see an
`Observation`. That's the one thing that lets this double as an RL environment or
a concurrent simulation without changes.

## Things I learned or got wrong first

Globally-unique disk sizes remove ties. A has odds, B has evens, so any two disks
have a strict order, even across players on the shared pole. No tie-breaking on
equal sizes is ever needed.

Frozen isn't deeply immutable. My first `GameState` stored the poles in a dict. A
frozen pydantic model stops you reassigning the attribute but not mutating the
dict in place (`state.poles[p] = ...` still worked). I switched to one tuple
field per pole, which makes it genuinely immutable with no extra code.

A win can be triggered by the opponent. Since the win only looks at your own
visible poles, the other player's move can complete it: B lifting a stray disk
off the shared pole clears it and wins for A. So the engine checks both players
after every step, not just the mover.

An empty board isn't a win. If your disks get stranded on the hidden side and
pole 3 ends up empty, the "pole 3 non-empty" clause correctly says no win. That's
a lost position, not a victory.

The simultaneous-win tie can't actually happen. Finishing a win needs the shared
pole empty and an empty hand, and a single move can't leave both players newly in
that state. I check the mover first so the "mover wins" rule is there, but it's
effectively dead code.

## Snags

Test-first vs a pytest pre-commit hook. If the hook runs the tests, it rejects
the deliberately-failing "red" commit. I moved the suite to CI and kept
pre-commit to fast checks (ruff + hygiene), which is the usual split and also
lets the history show a clean red-then-green per feature.

CI check naming. Branch protection wanted a check called `Lint` while the job
reported as `Lint (ruff)`; the mismatch silently blocked merges until I renamed
the job.

## Performance and limits

Replaying 1,000,000 moves took about 14s and ~1.1GB here, because every step
builds a fresh immutable state. For a hot RL loop that's the first thing to
optimise (see Future work in the README). There's also no upper bound on N, so a
huge N will run out of memory; a real service would cap it.

## Tests

95 tests, ~97% coverage: engine units, property-based invariants (disk
conservation, pole ordering, hand <= 1) checked after random and legal move
sequences, and frontend tests for the parser, the random player, and both CLI
commands.
