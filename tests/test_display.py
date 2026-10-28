"""Smoke tests for the pygame display, using SDL's headless drivers."""

import os

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from schroedingerchess.chess import LightBoard  # noqa: E402
from schroedingerchess.display import ChessDisplay  # noqa: E402
from schroedingerchess.game_engines import GameEngine  # noqa: E402


@pytest.fixture
def display():
    engine = GameEngine()
    engine.lightBoard = LightBoard()
    engine.display = ChessDisplay(engine)
    return engine.display


def test_menu(display):
    display.update()


def test_board(display):
    lb = LightBoard()
    lb.move(4, 1, 4, 3)
    display.setLastMove(4, 1, 4, 3)
    display.drawBoard(lb)
    display.addMessage("A message long enough to be split over several lines " * 3)
    display.flipDisplay(True)
    display.drawBoard(lb)
