"""Typer CLI: `hanoi replay` and `hanoi random`."""

from pathlib import Path
from random import Random
from typing import Annotated

import typer
from rich.console import Console

from hanoi.cli.render import render_board
from hanoi.engine import GameState, Player, initial_state, observe, step
from hanoi.io import ReplayParseError, parse_replay
from hanoi.players import choose_action

app = typer.Typer(
    help="Hanoi Crossing — replay and random-play frontends.",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()


@app.command()
def replay(file: Annotated[Path, typer.Argument(help="Path to a moves DSL file.")]) -> None:
    """Replay a recorded moves file; print the final state (board + JSON)."""
    try:
        game = parse_replay(file.read_text())
    except (OSError, ReplayParseError) as exc:
        console.print(f"[red]error:[/] {exc}")
        raise typer.Exit(code=1) from exc

    state = initial_state(game.n)
    illegal = 0
    for move in game.moves:
        result = step(state, move.player, move.action)
        if not result.was_legal:
            illegal += 1
        state = result.state
        if result.terminal:
            break
    _report(state, steps=len(game.moves), illegal=illegal)


@app.command()
def random(
    n: Annotated[int, typer.Option(help="Disks per player.")] = 3,
    seed: Annotated[int, typer.Option(help="RNG seed (reproducible).")] = 0,
    turn_order: Annotated[str, typer.Option(help="alternate | random")] = "alternate",
    max_steps: Annotated[int, typer.Option(help="Safety cap on steps.")] = 1000,
) -> None:
    """Both players make random legal moves until a win or max-steps."""
    if turn_order not in ("alternate", "random"):
        console.print("[red]error:[/] --turn-order must be 'alternate' or 'random'")
        raise typer.Exit(code=1)

    rng = Random(seed)
    state = initial_state(n)
    steps = 0
    for i in range(max_steps):
        if state.terminal:
            break
        player = _next_player(turn_order, i, rng)
        action = choose_action(observe(state, player), rng)
        state = step(state, player, action).state
        steps += 1
    _report(state, steps=steps, illegal=0)


def _next_player(turn_order: str, i: int, rng: Random) -> Player:
    if turn_order == "random":
        return rng.choice((Player.A, Player.B))
    return Player.A if i % 2 == 0 else Player.B


def _report(state: GameState, *, steps: int, illegal: int) -> None:
    console.print(render_board(state))
    outcome = f"winner: {state.winner.value}" if state.winner else "no winner"
    console.print(f"steps: {steps}   illegal moves: {illegal}   {outcome}")
    console.print_json(state.model_dump_json())
