"""Immutable full game state and the starting position.

Design contract (see docs/DESIGN.md, docs/design-decisions/):
- `GameState` is the god's-eye view: all five physical poles, both hands,
  and terminal/winner flags. It is a frozen pydantic model — never mutate it;
  build a new one (use `model_copy` at boundaries, `model_construct` on the
  trusted hot path in rules.py).
- Player A starts with odd disks (1, 3, ..., 2N-1) on pole A1; player B with
  even disks (2, 4, ..., 2N) on pole B1; largest at the bottom.
- Poles store disks bottom -> top; the last element is the top disk.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict

# A player's local pole index: 1 = own pole 1, 2 = SHARED middle, 3 = own pole 3.
LocalPole = Literal[1, 2, 3]


class Player(StrEnum):
    """The two players."""

    A = "A"
    B = "B"


class Pole(StrEnum):
    """Physical poles. SHARED (the middle pole) is visible to both players."""

    A1 = "A1"
    A3 = "A3"
    B1 = "B1"
    B3 = "B3"
    SHARED = "SHARED"


# maps the Pole enum to the GameState field name
_POLE_FIELD: dict[Pole, str] = {
    Pole.A1: "a1",
    Pole.A3: "a3",
    Pole.B1: "b1",
    Pole.B3: "b3",
    Pole.SHARED: "shared",
}


def physical_pole(player: Player, local: LocalPole) -> Pole:
    """Map a player's local pole (1/2/3) to a physical pole.

    Local pole 2 is SHARED for both players; 1 and 3 map to that player's
    own poles. This mapping is what enforces visibility structurally.
    """

    match player:
        case Player.A:
            match local:
                case 1:
                    return Pole.A1
                case 2:
                    return Pole.SHARED
                case 3:
                    return Pole.A3
                case _:
                    raise ValueError(f"invalid local pole {local}")
        case Player.B:
            match local:
                case 1:
                    return Pole.B1
                case 2:
                    return Pole.SHARED
                case 3:
                    return Pole.B3
                case _:
                    raise ValueError(f"invalid local pole {local}")
        case _:
            raise ValueError(f"unknown player {player}")


class GameState(BaseModel):
    """Immutable full game state (god's-eye view)."""

    model_config = ConfigDict(frozen=True)

    n: int
    a1: tuple[int, ...] = ()
    a3: tuple[int, ...] = ()
    b1: tuple[int, ...] = ()
    b3: tuple[int, ...] = ()
    shared: tuple[int, ...] = ()
    hand_a: int | None = None
    hand_b: int | None = None
    terminal: bool = False
    winner: Player | None = None

    def stack(self, pole: Pole) -> tuple[int, ...]:
        """The disk stack on `pole`, bottom -> top (() if empty)."""
        return getattr(self, _POLE_FIELD[pole])

    def top(self, pole: Pole) -> int | None:
        """Top disk on `pole`, or None if empty."""
        s = self.stack(pole)
        return s[-1] if s else None

    def hand(self, player: Player) -> int | None:
        """The disk `player` is holding, or None."""
        return self.hand_a if player is Player.A else self.hand_b

    def _with_pole(self, pole: Pole, stack: tuple[int, ...]) -> GameState:
        """New state with `pole` replaced. Private — engine use only."""
        return self.model_copy(update={_POLE_FIELD[pole]: stack})

    def _with_hand(self, player: Player, disk: int | None) -> GameState:
        """New state with `player`'s hand replaced. Private — engine use only."""
        return self.model_copy(update={"hand_a" if player is Player.A else "hand_b": disk})


def initial_state(n: int) -> GameState:
    """Build the starting position for a game with N disks per player.

    A: odd sizes 1, 3, ..., 2N-1 on A1 (largest at bottom).
    B: even sizes 2, 4, ..., 2N on B1 (largest at bottom).
    All other poles empty, both hands empty, not terminal.
    """
    if n < 1:
        raise ValueError("N cannot be less than 1")
    return GameState(n=n, a1=tuple(range(2 * n - 1, -1, -2)), b1=tuple(range(2 * n, 0, -2)))
