"""Tests for the player observation (hanoi.engine.observation).

An observation is a player's egocentric view: their pole 1/2/3 (2 = SHARED)
and their own hand. It must never expose the opponent's hidden poles or hand.
"""

import pytest
from pydantic import ValidationError

from hanoi.engine.observation import Observation, observe
from hanoi.engine.state import GameState, Player, initial_state


def test_observe_returns_own_poles_and_hand():
    s = initial_state(2)  # a1=(3, 1), b1=(4, 2)
    obs = observe(s, Player.A)
    assert obs.pole1 == (3, 1)  # A's own pole 1
    assert obs.pole3 == ()  # A's pole 3 empty
    assert obs.pole2 == ()  # shared empty
    assert obs.hand is None
    assert obs.n == 2


def test_each_player_sees_their_own_pole1():
    s = initial_state(2)
    assert observe(s, Player.A).pole1 == (3, 1)  # A1
    assert observe(s, Player.B).pole1 == (4, 2)  # B1


def test_pole2_is_the_shared_pole_for_both_players():
    # A disk on SHARED is visible identically to both players.
    s = GameState(n=2, a1=(3,), b1=(4,), shared=(1,))
    assert observe(s, Player.A).pole2 == (1,)
    assert observe(s, Player.B).pole2 == (1,)


def test_observation_hides_opponents_poles_and_hand():
    # A placed disk 1 on SHARED; B holds disk 2 and stranded disk 4 on B3.
    s = GameState(n=2, a1=(3,), b1=(), shared=(1,), b3=(4,), hand_b=2)
    obs_a = observe(s, Player.A)

    # A sees only its own side + the shared pole.
    assert obs_a.pole1 == (3,)
    assert obs_a.pole3 == ()
    assert obs_a.pole2 == (1,)
    assert obs_a.hand is None

    # B's stranded disk (4) and B's held disk (2) are nowhere in A's view.
    seen_by_a = obs_a.pole1 + obs_a.pole2 + obs_a.pole3
    assert 4 not in seen_by_a
    assert 2 not in seen_by_a

    # There is structurally no field exposing the opponent's side.
    assert not hasattr(obs_a, "b3")
    assert not hasattr(obs_a, "hand_b")

    # B, meanwhile, sees its own hand and stranded disk.
    obs_b = observe(s, Player.B)
    assert obs_b.pole3 == (4,)
    assert obs_b.hand == 2


def test_observation_is_immutable():
    obs = observe(initial_state(2), Player.A)
    with pytest.raises(ValidationError):
        obs.hand = 9


def test_observation_json_round_trips():
    obs = observe(GameState(n=2, a1=(3,), shared=(1,), hand_a=2), Player.A)
    restored = Observation.model_validate_json(obs.model_dump_json())
    assert restored == obs
