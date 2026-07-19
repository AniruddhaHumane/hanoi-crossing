"""Tests for the game rules (hanoi.engine.rules): is_win, legal_actions, step.

States are built directly with GameState where a specific position is needed;
initial_state is used for the natural starting board.
"""

import pytest

from hanoi.engine.actions import Lift, Place, Skip
from hanoi.engine.observation import observe
from hanoi.engine.rules import StepResult, is_win, legal_actions, step
from hanoi.engine.state import GameState, Player, initial_state

# --------------------------------------------------------------------------- #
# is_win  (literal / visible-only: hand empty, pole1 empty, SHARED empty, pole3 non-empty)
# --------------------------------------------------------------------------- #


def test_initial_state_is_not_a_win():
    s = initial_state(2)
    assert not is_win(s, Player.A)
    assert not is_win(s, Player.B)


def test_is_win_true_when_only_pole3_has_disks():
    s = GameState(n=2, a1=(), a3=(3, 1), shared=(), b1=(4, 2))
    assert is_win(s, Player.A)


@pytest.mark.parametrize(
    "override",
    [
        {"a1": (5,)},  # own pole 1 not empty
        {"shared": (2,)},  # shared not empty
        {"hand_a": 1},  # holding a disk
        {"a3": ()},  # pole 3 empty
    ],
)
def test_is_win_false_when_any_clause_fails(override):
    base = {"n": 3, "a1": (), "a3": (3, 1), "shared": (), "hand_a": None}
    assert not is_win(GameState(**{**base, **override}), Player.A)


def test_is_win_is_per_player():
    s = GameState(n=2, b1=(), b3=(4, 2), shared=(), a1=(3, 1))
    assert is_win(s, Player.B)
    assert not is_win(s, Player.A)


# --------------------------------------------------------------------------- #
# legal_actions  (pure on the observation)
# --------------------------------------------------------------------------- #


def test_legal_actions_from_initial_observation():
    obs = observe(initial_state(2), Player.A)  # hand empty; only pole1 has disks
    acts = legal_actions(obs)
    assert Skip() in acts
    assert Lift(pole=1) in acts
    assert Lift(pole=2) not in acts  # shared empty
    assert Lift(pole=3) not in acts  # pole3 empty
    assert all(not isinstance(a, Place) for a in acts)  # empty hand -> no place


def test_legal_actions_when_holding_a_disk():
    # holding disk 2: pole1 top=3 (2<3 ok), pole2 empty (ok), pole3 top=1 (2<1 no)
    s = GameState(n=2, a1=(3,), a3=(1,), shared=(), hand_a=2)
    acts = legal_actions(observe(s, Player.A))
    assert Skip() in acts
    assert Place(pole=1) in acts
    assert Place(pole=2) in acts
    assert Place(pole=3) not in acts
    assert all(not isinstance(a, Lift) for a in acts)  # holding -> no lift


def test_skip_is_always_legal():
    assert Skip() in legal_actions(observe(initial_state(1), Player.A))


# --------------------------------------------------------------------------- #
# step: legal moves
# --------------------------------------------------------------------------- #


def test_step_lift_moves_top_disk_into_hand():
    r = step(initial_state(2), Player.A, Lift(pole=1))  # a1 = (3, 1)
    assert r.was_legal
    assert r.state.hand(Player.A) == 1
    assert r.state.a1 == (3,)
    assert not r.terminal


def test_step_place_puts_held_disk_on_pole():
    r = step(GameState(n=2, a1=(3,), hand_a=1), Player.A, Place(pole=3))
    assert r.was_legal
    assert r.state.a3 == (1,)
    assert r.state.hand(Player.A) is None


def test_step_skip_is_legal_and_changes_nothing():
    s = initial_state(2)
    r = step(s, Player.A, Skip())
    assert r.was_legal
    assert r.state == s
    assert not r.terminal


def test_step_is_player_relative():
    r = step(initial_state(2), Player.B, Lift(pole=1))  # B lifts from B1, not A1
    assert r.state.b1 == (4,)
    assert r.state.a1 == (3, 1)
    assert r.state.hand(Player.B) == 2


def test_step_does_not_mutate_original_state():
    s = initial_state(2)
    step(s, Player.A, Lift(pole=1))
    assert s.a1 == (3, 1)
    assert s.hand(Player.A) is None


# --------------------------------------------------------------------------- #
# step: illegal moves waste the turn (state unchanged)
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "state, action",
    [
        (initial_state(2), Lift(pole=2)),  # lift from empty shared
        (initial_state(2), Place(pole=1)),  # place with empty hand
        (GameState(n=2, a1=(3,), hand_a=1), Lift(pole=1)),  # lift while holding
        (GameState(n=2, a1=(1,), hand_a=3), Place(pole=1)),  # place 3 onto 1
    ],
)
def test_step_illegal_action_leaves_state_unchanged(state, action):
    r = step(state, Player.A, action)
    assert not r.was_legal
    assert r.state == state
    assert not r.terminal


# --------------------------------------------------------------------------- #
# step: winning and terminal freeze
# --------------------------------------------------------------------------- #


def test_step_win_on_own_move():
    # A holds 1; a1 empty, shared empty, a3=(3,); placing 1 on a3 completes the win.
    s = GameState(n=2, a1=(), a3=(3,), shared=(), hand_a=1, b1=(4, 2))
    r = step(s, Player.A, Place(pole=3))
    assert r.was_legal and r.terminal
    assert r.winner == Player.A
    assert r.state.terminal and r.state.winner == Player.A


def test_step_win_triggered_by_opponent_move():
    # A is one stranded disk away (shared=(2,)); B lifting it off shared wins it for A.
    s = GameState(n=2, a1=(), a3=(3, 1), shared=(2,), b1=(4,))
    r = step(s, Player.B, Lift(pole=2))
    assert r.was_legal and r.terminal
    assert r.winner == Player.A


def test_step_on_terminal_state_is_a_noop():
    s = GameState(n=2, a3=(3, 1), b1=(4, 2), terminal=True, winner=Player.A)
    r = step(s, Player.A, Lift(pole=3))
    assert not r.was_legal
    assert r.state == s
    assert r.terminal and r.winner == Player.A


# --------------------------------------------------------------------------- #
# spec example
# --------------------------------------------------------------------------- #


def test_spec_n1_example_a_wins():
    # Turn order [A, B, A]: A lift 1, B lift 1, A place 3 -> A wins.
    s = initial_state(1)
    s = step(s, Player.A, Lift(pole=1)).state
    s = step(s, Player.B, Lift(pole=1)).state
    r = step(s, Player.A, Place(pole=3))
    assert r.terminal
    assert r.winner == Player.A


def test_step_result_is_the_documented_shape():
    r = step(initial_state(2), Player.A, Skip())
    assert isinstance(r, StepResult)
    assert {r.was_legal, r.terminal} <= {True, False}
    assert r.winner is None
