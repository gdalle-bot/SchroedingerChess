"""Tests for the export of games."""

import os

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from PIL import Image  # noqa: E402

from schroedingerchess import export  # noqa: E402
from schroedingerchess.chess import ChessBoard, LightBoard  # noqa: E402
from schroedingerchess.display import ChessDisplay  # noqa: E402
from schroedingerchess.game_engines import GameEngine  # noqa: E402

MOVES = [(4, 1, 4, 3), (4, 6, 4, 4), (6, 0, 5, 2), (1, 7, 2, 5)]


def test_move_names():
    assert export.move_name((4, 1, 4, 3)) == "e2e4"
    assert export.parse_move("g8f6") == (6, 7, 5, 5)
    with pytest.raises(ValueError):
        export.parse_move("Nf3")


def test_game_record_roundtrip():
    record = export.game_record(MOVES)
    assert "1. e2e4 e7e5 2. g1f3 b8c6 *" in record
    assert '[Result "*"]' in record
    assert export.read_game_record(record) == MOVES


def test_game_record_long_game_wraps():
    moves = [(1, 0, 2, 2), (6, 7, 5, 5), (2, 2, 1, 0), (5, 5, 6, 7)] * 20
    record = export.game_record(moves, outcome="Draw by the 50-move rule")
    assert all(len(line) <= 80 for line in record.splitlines())
    assert '[Result "1/2-1/2"]' in record
    assert "{Draw by the 50-move rule}" in record
    assert export.read_game_record(record) == moves


@pytest.mark.parametrize(
    ("outcome", "to_move", "tag"),
    [
        ("Current player checkmated", 1, "1-0"),
        ("Current player checkmated", 0, "0-1"),
        ("Stalemate", 0, "1/2-1/2"),
        ("Result unclear: checkmate in 33% ...", 1, "*"),
        ("Legal moves still exist", 0, "*"),
    ],
)
def test_result_tag(outcome, to_move, tag):
    assert export.result_tag(outcome, to_move) == tag


def test_replay():
    cb = export.replay(MOVES)
    assert isinstance(cb, ChessBoard) and cb.time == 4


@pytest.fixture
def display():
    engine = GameEngine()
    engine.lightBoard = LightBoard()
    engine.display = ChessDisplay(engine)
    return engine.display


def test_export_gif(display, tmp_path):
    path = export.export_gif(MOVES, str(tmp_path / "game.gif"), display)
    with Image.open(path) as image:
        assert image.n_frames == len(MOVES) + 1
        assert image.size[0] == 480


def test_gui_exports(display, tmp_path):
    display.state, display.mode = "PLAYING", "LOCAL"
    for move in MOVES:
        display.setLastMove(*move)
    text = display.exportText(str(tmp_path / "game.pgn"))
    with open(text, encoding="utf-8") as file:
        assert export.read_game_record(file.read()) == MOVES
    gif = display.exportGif(str(tmp_path / "game.gif"))
    assert os.path.getsize(gif) > 0
    assert "Animation saved" in " ".join(display.message_history[-3:])


def test_export_name(tmp_path):
    path = export.export_name("pgn", str(tmp_path))
    assert path.startswith(str(tmp_path)) and path.endswith(".pgn")
