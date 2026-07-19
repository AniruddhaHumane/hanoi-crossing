"""Human-readable rendering of a game state (god's-eye, for the replay tool)."""

from hanoi.engine import GameState


def _fmt(stack: tuple[int, ...]) -> str:
    return ", ".join(str(d) for d in stack) if stack else "-"


def _hand(disk: int | None) -> str:
    return str(disk) if disk is not None else "-"


def render_board(state: GameState) -> str:
    """A compact ASCII view of the full board (bottom -> top per pole)."""
    return "\n".join(
        [
            f"  A1: {_fmt(state.a1):<14} A3: {_fmt(state.a3):<14} hand A: {_hand(state.hand_a)}",
            f"  SHARED: {_fmt(state.shared)}",
            f"  B1: {_fmt(state.b1):<14} B3: {_fmt(state.b3):<14} hand B: {_hand(state.hand_b)}",
        ]
    )
