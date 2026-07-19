"""A player's egocentric, partial view of the game.

Only the observer's own poles (1/2/3, where 2 = SHARED) and their hand — never
the opponent's hidden poles or hand. This is the sole thing an agent receives,
so hidden information is enforced structurally (there is no field for the
opponent's side).
"""

from pydantic import BaseModel, ConfigDict

from hanoi.engine.state import GameState, Player, physical_pole


class Observation(BaseModel):
    """What a player sees when choosing a move."""

    model_config = ConfigDict(frozen=True)

    pole1: tuple[int, ...]  # observer's own pole 1
    pole2: tuple[int, ...]  # SHARED (visible to both players)
    pole3: tuple[int, ...]  # observer's own pole 3
    hand: int | None  # observer's held disk, or None
    n: int  # board size (public)


def observe(state: GameState, player: Player) -> Observation:
    """Project the full state onto `player`'s egocentric view.

    Map the player's local poles 1/2/3 to physical poles via
    `physical_pole(player, local)` (2 -> SHARED), read each stack plus the
    player's hand and the board size `n`. Do not read the opponent's poles.
    """

    return Observation(
        pole1=state.stack(physical_pole(player, 1)),  # own pole 1
        pole2=state.stack(physical_pole(player, 2)),  # SHARED
        pole3=state.stack(physical_pole(player, 3)),  # own pole 3
        hand=state.hand(player),
        n=state.n,
    )
