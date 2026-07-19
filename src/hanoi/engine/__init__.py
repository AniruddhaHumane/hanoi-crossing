"""Pure, immutable game core for Hanoi Crossing.

This package must stay under 500 lines and free of I/O, global RNG, and
mutation. See the README and docs/design-decisions/ for the design.

Public API — consumers should import from here:

    from hanoi.engine import initial_state, observe, legal_actions, step, is_win
"""

from hanoi.engine.actions import Action, Lift, Place, Skip
from hanoi.engine.observation import Observation, observe
from hanoi.engine.rules import StepResult, is_win, legal_actions, step
from hanoi.engine.state import (
    GameState,
    Player,
    Pole,
    initial_state,
    physical_pole,
)

__all__ = [
    "Action",
    "GameState",
    "Lift",
    "Observation",
    "Place",
    "Player",
    "Pole",
    "Skip",
    "StepResult",
    "initial_state",
    "is_win",
    "legal_actions",
    "observe",
    "physical_pole",
    "step",
]
