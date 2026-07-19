"""Tests for the replay DSL parser (hanoi.io.dsl)."""

import pytest

from hanoi.engine import Lift, Place, Player, Skip
from hanoi.io import Move, parse_replay
from hanoi.io.dsl import ReplayParseError


def test_parses_spec_n1_example():
    text = "# spec N=1\nn 1\nA lift 1\nB lift 1\nA place 3\n"
    replay = parse_replay(text)
    assert replay.n == 1
    assert replay.moves == (
        Move(player=Player.A, action=Lift(pole=1)),
        Move(player=Player.B, action=Lift(pole=1)),
        Move(player=Player.A, action=Place(pole=3)),
    )


def test_ignores_comments_and_blank_lines():
    text = "\n# header follows\nn 2\n\nA skip   # inline comment\n"
    replay = parse_replay(text)
    assert replay.n == 2
    assert replay.moves == (Move(player=Player.A, action=Skip()),)


def test_player_and_verb_are_case_insensitive():
    replay = parse_replay("n 1\na LIFT 1\n")
    assert replay.moves[0] == Move(player=Player.A, action=Lift(pole=1))


@pytest.mark.parametrize(
    "text, needle",
    [
        ("A lift 1\n", "header"),  # missing n header
        ("n zero\n", "integer"),  # non-integer N
        ("n 0\n", ">= 1"),  # N < 1
        ("n 1\nC lift 1\n", "unknown player"),  # bad player
        ("n 1\nA jump 1\n", "unknown verb"),  # bad verb
        ("n 1\nA lift\n", "needs a pole"),  # lift without pole
        ("n 1\nA skip 1\n", "takes no pole"),  # skip with a pole
        ("n 1\nA lift 9\n", "1/2/3"),  # pole out of range
        ("n 1\nA lift x\n", "integer"),  # pole not an integer
    ],
)
def test_malformed_input_raises_with_context(text, needle):
    with pytest.raises(ReplayParseError) as exc:
        parse_replay(text)
    assert needle in str(exc.value)
