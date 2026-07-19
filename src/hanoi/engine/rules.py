"""Game rules: legality, transitions, and win detection.

step(state, player, action) is the single pure transition. Illegal actions
waste the turn (state unchanged). After every legal move, both players are
checked for a win; the first winner freezes the game (actor wins any tie).
"""

from pydantic import BaseModel, ConfigDict

from hanoi.engine.actions import Action, Lift, Place, Skip
from hanoi.engine.observation import Observation, observe
from hanoi.engine.state import GameState, Player, physical_pole


class StepResult(BaseModel):
    """Outcome of a transition: the new state plus what happened."""

    model_config = ConfigDict(frozen=True)

    state: GameState
    was_legal: bool
    terminal: bool = False
    winner: Player | None = None


def is_win(state: GameState, player: Player) -> bool:
    """Literal / visible-only win for `player`.

    True iff: hand empty, own pole 1 empty, SHARED empty, own pole 3 non-empty.
    """

    return (
        state.hand(player) is None
        and not state.stack(physical_pole(player, 1))
        and not state.stack(physical_pole(player, 2))
        and bool(state.stack(physical_pole(player, 3)))
    )


def legal_actions(obs: Observation) -> list[Action]:
    """All legal actions given a player's observation.

    - Skip is always legal.
    - If the hand is empty: Lift(i) for each non-empty visible pole i.
    - If holding a disk: Place(i) where pole i is empty or held < its top disk.
    """
    actions = [Skip()]
    if obs.hand is None:
        if len(obs.pole1) > 0:
            actions.append(Lift(pole=1))
        if len(obs.pole2) > 0:
            actions.append(Lift(pole=2))
        if len(obs.pole3) > 0:
            actions.append(Lift(pole=3))
    else:
        if len(obs.pole1) == 0 or obs.hand < obs.pole1[-1]:
            actions.append(Place(pole=1))
        if len(obs.pole2) == 0 or obs.hand < obs.pole2[-1]:
            actions.append(Place(pole=2))
        if len(obs.pole3) == 0 or obs.hand < obs.pole3[-1]:
            actions.append(Place(pole=3))

    return actions


def step(state: GameState, player: Player, action: Action) -> StepResult:
    """Apply `action` for `player`; return the new state and what happened.

    1. If the state is terminal, it is frozen: return it unchanged, was_legal=False.
    2. If the action is not in legal_actions(observe(state, player)), the turn is
       wasted: return the state unchanged, was_legal=False.
    3. Otherwise apply it (Skip / Lift / Place) via the private copy-on-write
       helpers, mapping the local pole with physical_pole(player, action.pole).
    4. Check for a win, actor first (tie-break), then the opponent; the first
       winner freezes the game (terminal=True, winner set on the new state).
    """
    if state.terminal:
        return StepResult(state=state, was_legal=False, terminal=True, winner=state.winner)
    if action not in legal_actions(observe(state, player)):
        return StepResult(state=state, was_legal=False, terminal=False)
    match action.kind:
        case "skip":
            return StepResult(state=state, was_legal=True)
        case "lift":
            pole = physical_pole(player, action.pole)
            stack = state.stack(pole)
            state = state._with_pole(pole, stack[:-1])._with_hand(player, stack[-1])
        case "place":
            pole = physical_pole(player, action.pole)
            stack = state.stack(pole)
            state = state._with_pole(pole, (*stack, state.hand(player)))._with_hand(player, None)
        case _:
            raise ValueError("invalid action")
    opponent = Player.B if player is Player.A else Player.A
    winner = player if is_win(state, player) else opponent if is_win(state, opponent) else None
    if winner is not None:
        state = state.model_copy(update={"terminal": True, "winner": winner})
    return StepResult(state=state, was_legal=True, terminal=winner is not None, winner=winner)
