"""Tests for the random policy (hanoi.players)."""

from random import Random

from hanoi.engine import Player, initial_state, legal_actions, observe
from hanoi.players import choose_action


def test_choose_action_is_deterministic_for_a_seed():
    obs = observe(initial_state(3), Player.A)
    assert choose_action(obs, Random(42)) == choose_action(obs, Random(42))


def test_choice_is_always_legal():
    rng = Random(1)
    obs = observe(initial_state(3), Player.A)
    for _ in range(20):
        assert choose_action(obs, rng) in legal_actions(obs)
