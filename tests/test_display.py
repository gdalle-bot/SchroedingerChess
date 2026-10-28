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


def test_illegal_move_banner(display):
    click(display, display._menu_buttons()["local"].rect.center)
    engine = display.gameEngine
    # The knight on b1 tries to go to b3
    click(display, (1 * 80 + 40, 7 * 80 + 40))
    click(display, (1 * 80 + 40, 5 * 80 + 40))
    assert display.attempted_move == (1, 0, 1, 2)
    engine.moveTask(display.attempted_move)  # what the reactor would run
    assert "b1 to b3 is blocked" in display.error
    assert display._error_alpha() > 0
    assert len(display.message_history) - 1 in display.error_lines
    display.render()
    # A legal move clears the banner
    engine.moveTask((4, 1, 4, 3))
    assert display.error is None and display.attempted_move is None


def test_menu_error_banner(display):
    click(display, display._menu_buttons()["online"].rect.center)
    display.address.text = "nowhere"
    click(display, display._menu_buttons()["connect"].rect.center)
    assert display.state == "MENU"
    assert "valid address" in display.error


def test_online_move_message(display):
    # Regression: the move of white was announced as a move of black
    from schroedingerchess.game_engines import OnePlayerOnNetwork

    engine = OnePlayerOnNetwork.__new__(OnePlayerOnNetwork)
    engine.display, engine.lightBoard, engine.turn = display, LightBoard(), 0
    display.gameEngine = engine
    engine.handleMove((4, 1, 4, 3))
    assert display.message_history[-1] == "White: e2-e4"
    assert engine.turn == 1


@pytest.mark.parametrize(("highdpi", "scale"), [("1", None), ("0", "2"), ("1", "2")])
def test_high_resolution(monkeypatch, highdpi, scale):
    # The renderer path is used on macOS, the scale is 2 on Retina screens
    monkeypatch.setenv("SCHROEDINGERCHESS_HIGHDPI", highdpi)
    if scale is not None:
        monkeypatch.setenv("SCHROEDINGERCHESS_SCALE", scale)
    engine = GameEngine()
    engine.lightBoard = LightBoard()
    engine.loopingCall = FakeLoopingCall()
    engine.display = display = ChessDisplay(engine)
    factor = float(scale or 1)
    assert display.screen.get_size() == (980 * factor, 640 * factor)
    # Layout and mouse positions stay in points
    click(display, display._menu_buttons()["local"].rect.center)
    assert display.state == "PLAYING"
    assert display._picture("wS", 80).get_size() == (80 * factor, 80 * factor)
    display.showError("Something went wrong")
    display.render()


@pytest.mark.parametrize("clock", [0, 1, 85, 99, 100])
def test_fifty_move_countdown(display, clock):
    click(display, display._menu_buttons()["local"].rect.center)
    display.gameEngine.lightBoard.halfmove_clock = clock
    display.lightBoard = display.gameEngine.lightBoard
    display.render()


def square(x, y):
    """Center of the square ``(x, y)`` on the screen, white at the bottom."""
    return (x * 80 + 40, (7 - y) * 80 + 40)


def test_selection_rules(display):
    click(display, display._menu_buttons()["local"].rect.center)
    # Empty squares and black pieces cannot be selected by white
    click(display, square(4, 4))
    assert display.selectedBox is None
    click(display, square(4, 6))
    assert display.selectedBox is None
    # A white piece can, and clicking it again deselects it
    click(display, square(4, 1))
    assert display.selectedBox == (4, 6)
    click(display, square(4, 1))
    assert display.selectedBox is None
    # Clicking another white piece switches the selection
    click(display, square(4, 1))
    click(display, square(3, 1))
    assert display.selectedBox == (3, 6)
    assert display.attempted_move is None
    # Then a destination square triggers a move
    click(display, square(3, 3))
    assert display.attempted_move == (3, 1, 3, 3)
    display.gameEngine.moveTask(display.attempted_move)
    # Now black can be selected, but not white
    click(display, square(3, 3))
    assert display.selectedBox is None
    click(display, square(4, 6))
    assert display.selectedBox == (4, 1)


def test_online_selection(display):
    from schroedingerchess.game_engines import OnePlayerOnNetwork

    engine = OnePlayerOnNetwork.__new__(OnePlayerOnNetwork)
    engine.display, engine.lightBoard, engine.color = display, LightBoard(), 1
    display.gameEngine, display.state, display.mode = engine, "PLAYING", "ONLINE"
    display.lightBoard = engine.lightBoard
    engine.turn = -1  # waiting for an opponent
    assert not display.isSelectable(4, 6)
    engine.turn = 0  # white to move, but the user plays black
    assert not display.isSelectable(4, 1) and not display.isSelectable(4, 6)
    engine.turn = 1
    assert display.isSelectable(4, 6) and not display.isSelectable(4, 1)


def test_wrap_long_words():
    font = pygame.font.SysFont("arial", 15)
    path = "/Users/someone/Downloads/schroedinger-chess-20261028-171512.gif"
    lines = _wrap(f"Animation saved as {path}", font, 120)
    assert all(font.size(line)[0] <= 120 for line in lines)
    assert "".join(lines).replace(" ", "") == f"Animationsavedas{path}"
    assert _wrap("", font, 120) == [""]
