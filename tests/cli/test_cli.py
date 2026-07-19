"""Tests for the CLI frontends (hanoi.cli), driven via Typer's CliRunner."""

from typer.testing import CliRunner

from hanoi.cli import app

runner = CliRunner()


def test_replay_spec_n1_reports_a_wins(tmp_path):
    moves = tmp_path / "game.moves"
    moves.write_text("n 1\nA lift 1\nB lift 1\nA place 3\n")
    result = runner.invoke(app, ["replay", str(moves)])
    assert result.exit_code == 0
    assert "winner: A" in result.output


def test_replay_trace_prints_a_board_per_move(tmp_path):
    moves = tmp_path / "game.moves"
    moves.write_text("n 1\nA lift 1\nB lift 1\nA place 3\n")
    result = runner.invoke(app, ["replay", str(moves), "--trace"])
    assert result.exit_code == 0
    assert "initial position" in result.output
    assert "1. A lift 1" in result.output
    assert "3. A place 3" in result.output
    assert result.output.count("SHARED:") == 5  # initial + 3 moves + final report


def test_replay_reports_a_parse_error(tmp_path):
    moves = tmp_path / "bad.moves"
    moves.write_text("A lift 1\n")  # missing the n header
    result = runner.invoke(app, ["replay", str(moves)])
    assert result.exit_code == 1


def test_random_is_deterministic_for_a_seed():
    args = ["random", "--n", "3", "--seed", "7", "--max-steps", "200"]
    first = runner.invoke(app, args)
    second = runner.invoke(app, args)
    assert first.exit_code == 0
    assert first.output == second.output


def test_random_never_makes_an_illegal_move():
    result = runner.invoke(app, ["random", "--n", "3", "--seed", "3", "--max-steps", "200"])
    assert result.exit_code == 0
    assert "illegal moves: 0" in result.output


def test_random_rejects_bad_turn_order():
    result = runner.invoke(app, ["random", "--turn-order", "spiral"])
    assert result.exit_code == 1


def test_random_turn_order_runs_and_is_deterministic():
    args = ["random", "--turn-order", "random", "--seed", "5", "--max-steps", "200"]
    first = runner.invoke(app, args)
    second = runner.invoke(app, args)
    assert first.exit_code == 0
    assert first.output == second.output
