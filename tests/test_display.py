"""Smoke tests for the pygame display, using SDL's headless drivers."""

import os

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

from schroedingerchess.chess import LightBoard  # noqa: E402
from schroedingerchess.display import ChessDisplay, _wrap  # noqa: E402
from schroedingerchess.game_engines import GameEngine, square_name  # noqa: E402


class FakeLoopingCall:
    def start(self, interval):
        return self

    def stop(self):
        pass

    def addErrback(self, f):
        pass


@pytest.fixture
def display():
    engine = GameEngine()
    engine.lightBoard = LightBoard()
    engine.loopingCall = FakeLoopingCall()
    engine.display = ChessDisplay(engine)
    return engine.display


def click(display, pos):
    for kind in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
        pygame.event.post(pygame.event.Event(kind, button=1, pos=pos))
    display.update()


def test_menu(display):
    display.update()
    assert display.state == "MENU"


def test_online_menu(display):
    click(display, display._menu_buttons()["online"].rect.center)
    assert display.menuState == "ONLINE"
    click(display, display._menu_buttons()["black"].rect.center)
    assert display.selected_color == "B"
    click(display, display._menu_buttons()["back"].rect.center)
    assert display.menuState == "START"


def test_local_game(display):
    click(display, display._menu_buttons()["local"].rect.center)
    assert display.state == "PLAYING" and display.mode == "LOCAL"
    engine = display.gameEngine
    # Select e2, then click on e4 (white is at the bottom)
    click(display, (4 * 80 + 40, 6 * 80 + 40))
    assert display.selectedBox == (4, 6)
    click(display, (4 * 80 + 40, 4 * 80 + 40))
    assert display.selectedBox is None
    engine.moveTask((4, 1, 4, 3))  # what the reactor would run
    assert engine.chessBoard.moves == [(4, 1, 4, 3)]
    assert display._turn() == 1
    assert display.message_history[-1] == "White: e2-e4"
    click(display, display._pane_buttons()["flip"].rect.center)
    assert display.flip
    click(display, display._pane_buttons()["menu"].rect.center)
    assert display.state == "MENU"


def test_draw_pieces(display):
    lb = LightBoard()
    lb.move(4, 1, 4, 3)
    lb.setPiece(0, 0, (0, 0), ["Q", "R"])
    lb.setPiece(1, 0, False, ["N"])
    display.state = "PLAYING"
    display.setLastMove(4, 1, 4, 3)
    display.drawChecks([(4, 7)])
    display.drawBoard(lb)
    display.flipDisplay(True)
    display.drawBoard(lb)


def test_messages(display):
    display.addMessage("A message long enough to be split over several lines " * 3)
    assert len(display.message_history) > 3
    display.scrollMessages(-100)
    assert display.current_first_message == 0


def test_wrap():
    font = pygame.font.SysFont("arial", 15)
    lines = _wrap("one two three four five six", font, 60)
    assert " ".join(lines) == "one two three four five six"
    assert all(font.size(line)[0] <= 60 for line in lines)


@pytest.mark.parametrize(
    ("address", "valid"),
    [
        ("127.0.0.1:6000", True),
        ("localhost:6000", True),
        ("example.org:80", True),
        ("127.0.0.1", False),
        (":6000", False),
        ("localhost:port", False),
        ("localhost:70000", False),
    ],
)
def test_check_address_format(display, address, valid):
    assert display.check_address_format(address) == valid


def test_square_name():
    assert square_name(0, 0) == "a1"
    assert square_name(4, 3) == "e4"
