"""Tests for the immutable game state (hanoi.engine.state).

Each test does one thing and reads top-to-bottom: arrange a state, act, assert.
"""

import pytest
from pydantic import ValidationError

from hanoi.engine.state import (
    GameState,
    Player,
    Pole,
    initial_state,
    physical_pole,
)

# --------------------------------------------------------------------------- #
# initial_state: the starting position
# --------------------------------------------------------------------------- #


def test_initial_state_n1_matches_spec_example():
    # The spec's Example (N = 1): A has disk 1 on A1, B has disk 2 on B1.
    s = initial_state(1)
    assert s.a1 == (1,)
    assert s.b1 == (2,)
    assert s.a3 == () and s.b3 == () and s.shared == ()
    assert s.hand(Player.A) is None and s.hand(Player.B) is None
    assert s.terminal is False and s.winner is None
    assert s.n == 1


@pytest.mark.parametrize(
    "n, a1, b1",
    [
        (1, (1,), (2,)),
        (2, (3, 1), (4, 2)),
        (3, (5, 3, 1), (6, 4, 2)),
    ],
)
def test_initial_state_stacks_largest_at_bottom(n, a1, b1):
    # Poles store bottom -> top, so the largest disk comes first.
    s = initial_state(n)
    assert s.a1 == a1  # A gets the odd sizes
    assert s.b1 == b1  # B gets the even sizes


def test_initial_state_has_every_disk_exactly_once():
    # Invariant: sizes 1..2N each appear exactly once across the whole board.
    n = 4
    s = initial_state(n)
    everywhere = s.a1 + s.a3 + s.b1 + s.b3 + s.shared
    assert sorted(everywhere) == list(range(1, 2 * n + 1))


@pytest.mark.parametrize("bad_n", [0, -1, -5])
def test_initial_state_rejects_n_below_1(bad_n):
    with pytest.raises(ValueError):
        initial_state(bad_n)


# --------------------------------------------------------------------------- #
# physical_pole: player-relative pole (1/2/3) -> physical pole
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "player, local, expected",
    [
        (Player.A, 1, Pole.A1),
        (Player.A, 3, Pole.A3),
        (Player.B, 1, Pole.B1),
        (Player.B, 3, Pole.B3),
    ],
)
def test_physical_pole_maps_own_poles(player, local, expected):
    assert physical_pole(player, local) == expected


def test_physical_pole_local_2_is_shared_for_both_players():
    # The middle pole is the SAME physical pole for A and B.
    assert physical_pole(Player.A, 2) == Pole.SHARED
    assert physical_pole(Player.B, 2) == Pole.SHARED


@pytest.mark.parametrize("player", [Player.A, Player.B])
def test_physical_pole_rejects_invalid_local(player):
    with pytest.raises(ValueError):
        physical_pole(player, 4)  # only 1/2/3 are valid


# --------------------------------------------------------------------------- #
# accessors: stack / top / hand
# --------------------------------------------------------------------------- #


def test_stack_returns_full_pole_bottom_to_top():
    s = initial_state(2)
    assert s.stack(Pole.A1) == (3, 1)
    assert s.stack(Pole.SHARED) == ()  # empty pole -> empty tuple


def test_top_returns_top_disk_or_none():
    s = initial_state(2)
    assert s.top(Pole.A1) == 1  # last element is the top
    assert s.top(Pole.SHARED) is None  # empty pole -> None


def test_hand_is_empty_at_start():
    s = initial_state(2)
    assert s.hand(Player.A) is None
    assert s.hand(Player.B) is None


# --------------------------------------------------------------------------- #
# copy-on-write: produce a NEW state, leave the original untouched
# --------------------------------------------------------------------------- #


def test_with_pole_returns_new_state_and_leaves_original_untouched():
    s = initial_state(2)
    changed = s._with_pole(Pole.A1, (9,))
    assert changed.a1 == (9,)  # new state reflects the change
    assert s.a1 == (3, 1)  # original is unchanged
    assert changed is not s


def test_with_hand_only_changes_the_named_player():
    s = initial_state(2)
    changed = s._with_hand(Player.A, 7)
    assert changed.hand(Player.A) == 7
    assert changed.hand(Player.B) is None  # B untouched
    assert s.hand(Player.A) is None  # original untouched


def test_with_hand_can_clear_a_hand():
    holding = initial_state(2)._with_hand(Player.B, 4)
    cleared = holding._with_hand(Player.B, None)
    assert holding.hand(Player.B) == 4
    assert cleared.hand(Player.B) is None


# --------------------------------------------------------------------------- #
# immutability + serialization
# --------------------------------------------------------------------------- #


def test_state_fields_cannot_be_reassigned():
    s = initial_state(2)
    with pytest.raises(ValidationError):  # frozen model rejects reassignment
        s.a1 = (0,)


def test_json_round_trip_preserves_state():
    s = initial_state(3)._with_hand(Player.A, 5)
    restored = GameState.model_validate_json(s.model_dump_json())
    assert restored == s
