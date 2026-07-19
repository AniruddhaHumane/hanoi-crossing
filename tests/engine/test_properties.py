"""Property-based invariants for the engine (hanoi.engine).

Whatever sequence of (player, action) pairs is applied — legal, illegal, or
post-terminal — the core invariants must always hold: disks are conserved, every
pole stays strictly ordered, and a hand holds at most one disk.
"""

from random import Random

from hypothesis import given, settings
from hypothesis import strategies as st

from hanoi.engine import (
    GameState,
    Lift,
    Place,
    Player,
    Skip,
    initial_state,
    legal_actions,
    observe,
    step,
)

_players = st.sampled_from([Player.A, Player.B])
_poles = st.sampled_from([1, 2, 3])
_actions = st.one_of(
    _poles.map(lambda p: Lift(pole=p)),
    _poles.map(lambda p: Place(pole=p)),
    st.just(Skip()),
)
_sequences = st.lists(st.tuples(_players, _actions), max_size=60)


def _all_disks(state: GameState) -> list[int]:
    disks = list(state.a1 + state.a3 + state.b1 + state.b3 + state.shared)
    disks += [d for d in (state.hand_a, state.hand_b) if d is not None]
    return disks


def _check_invariants(state: GameState, n: int) -> None:
    # (a) conservation: every size 1..2N appears exactly once across the board.
    assert sorted(_all_disks(state)) == list(range(1, 2 * n + 1))
    # (b) every pole is strictly decreasing bottom -> top (largest at the bottom).
    for stack in (state.a1, state.a3, state.b1, state.b3, state.shared):
        assert all(stack[i] > stack[i + 1] for i in range(len(stack) - 1))
    # (c) a hand holds at most one disk.
    assert state.hand_a is None or isinstance(state.hand_a, int)
    assert state.hand_b is None or isinstance(state.hand_b, int)


@given(n=st.integers(min_value=1, max_value=5), seq=_sequences)
@settings(max_examples=200, deadline=None)
def test_invariants_hold_under_arbitrary_actions(n, seq):
    # Arbitrary (often illegal) actions must never corrupt the state.
    state = initial_state(n)
    _check_invariants(state, n)
    for player, action in seq:
        state = step(state, player, action).state
        _check_invariants(state, n)


@given(
    n=st.integers(min_value=1, max_value=4),
    seed=st.integers(),
    length=st.integers(min_value=0, max_value=80),
)
@settings(max_examples=100, deadline=None)
def test_invariants_hold_under_legal_play(n, seed, length):
    # Legal alternating play reaches valid deep states (and sometimes a win).
    rng = Random(seed)
    state = initial_state(n)
    for i in range(length):
        if state.terminal:
            break
        player = Player.A if i % 2 == 0 else Player.B
        action = rng.choice(legal_actions(observe(state, player)))
        state = step(state, player, action).state
        _check_invariants(state, n)
