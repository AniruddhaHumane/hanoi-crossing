"""Replay DSL: parse a self-contained moves file into a validated Replay.

Format::

    # comments start with '#'; blank lines are ignored
    n <N>                    # header (required, first non-comment line)
    <player> <verb> [pole]   # one move per line

  player : A | B  (case-insensitive)
  verb   : lift | place | skip   (lift/place take a pole 1/2/3; skip takes none)

The player column is the turn order — the engine assumes no pattern.
"""

from pydantic import BaseModel, ConfigDict

from hanoi.engine import Action, Lift, Place, Player, Skip


class ReplayParseError(ValueError):
    """Malformed replay input (message includes the 1-based line number)."""


class Move(BaseModel):
    """A single move: who acts and what they do."""

    model_config = ConfigDict(frozen=True)

    player: Player
    action: Action


class Replay(BaseModel):
    """A parsed, self-contained replay: board size + the move sequence."""

    model_config = ConfigDict(frozen=True)

    n: int
    moves: tuple[Move, ...]


_LIFT_PLACE = {"lift": Lift, "place": Place}


def parse_replay(text: str) -> Replay:
    """Parse replay DSL text into a Replay, or raise ReplayParseError."""
    n: int | None = None
    moves: list[Move] = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.split("#", 1)[0].strip()  # drop inline comments + whitespace
        if not line:
            continue
        tokens = line.split()
        if n is None:
            n = _parse_header(tokens, lineno, raw)
        else:
            moves.append(_parse_move(tokens, lineno, raw))
    if n is None:
        raise ReplayParseError("missing 'n <N>' header")
    return Replay(n=n, moves=tuple(moves))


def _parse_header(tokens: list[str], lineno: int, raw: str) -> int:
    if len(tokens) != 2 or tokens[0] != "n":
        raise ReplayParseError(f"line {lineno}: expected header 'n <N>', got {raw.strip()!r}")
    n = _parse_int(tokens[1], lineno, "N")
    if n < 1:
        raise ReplayParseError(f"line {lineno}: N must be >= 1, got {n}")
    return n


def _parse_move(tokens: list[str], lineno: int, raw: str) -> Move:
    player = _parse_player(tokens[0], lineno)
    if len(tokens) < 2:
        raise ReplayParseError(f"line {lineno}: missing verb: {raw.strip()!r}")
    verb = tokens[1].lower()
    if verb == "skip":
        if len(tokens) != 2:
            raise ReplayParseError(f"line {lineno}: 'skip' takes no pole: {raw.strip()!r}")
        return Move(player=player, action=Skip())
    if verb in _LIFT_PLACE:
        if len(tokens) != 3:
            raise ReplayParseError(f"line {lineno}: '{verb}' needs a pole 1/2/3: {raw.strip()!r}")
        pole = _parse_int(tokens[2], lineno, "pole")
        if pole not in (1, 2, 3):
            raise ReplayParseError(f"line {lineno}: pole must be 1/2/3, got {pole}")
        return Move(player=player, action=_LIFT_PLACE[verb](pole=pole))
    raise ReplayParseError(f"line {lineno}: unknown verb {tokens[1]!r}")


def _parse_player(tok: str, lineno: int) -> Player:
    try:
        return Player(tok.upper())
    except ValueError:
        raise ReplayParseError(f"line {lineno}: unknown player {tok!r} (expected A or B)") from None


def _parse_int(tok: str, lineno: int, what: str) -> int:
    try:
        return int(tok)
    except ValueError:
        raise ReplayParseError(f"line {lineno}: {what} must be an integer, got {tok!r}") from None
