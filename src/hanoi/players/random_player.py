"""A seeded random policy over (observation, legal actions).

Consumes ONLY the observation — never the full state — exactly as an external
RL agent or simulation client would. This is the proof the engine's public API
is sufficient for an agent that cannot see hidden information.
"""

from random import Random

from hanoi.engine import Action, Observation, legal_actions


def choose_action(obs: Observation, rng: Random) -> Action:
    """Pick a uniformly random legal action for the given observation.

    `legal_actions` always includes Skip, so there is always a choice.
    """
    return rng.choice(legal_actions(obs))
