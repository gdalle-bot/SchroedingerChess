"""Tests for the lightweight board and the client/server message handling."""

import json

import pytest

from schroedingerchess.chess import IllegalMove, LightBoard, major_piece_natures
from schroedingerchess.client import ChessClientProtocol
from schroedingerchess.server import ChessServerProtocol, Game


def test_lightboard_initial():
    lb = LightBoard()
    assert lb.getPiece(0, 0)["natures"] == major_piece_natures
    assert lb.getPiece(0, 1)["natures"] == ["P"]
    assert lb.getPiece(0, 7)["color"] == 1
    assert lb.getPiece(4, 4) is None
    assert lb.getPieceIndex(3, 6) == 24 + 8 + 3


def test_lightboard_move_and_capture():
    lb = LightBoard()
    lb.move(1, 0, 2, 2)
    assert lb.getPiece(2, 2)["natures"] == ["N"]
    assert lb.getPiece(1, 0) is None
    lb.move(2, 2, 3, 4)
    lb.move(3, 4, 4, 6)  # capture a black pawn
    assert lb.getDeadPieces(1) == [{"position": False, "color": 1, "natures": ["P"]}]


def test_lightboard_move_keeps_other_natures():
    # Regression: other pieces used to be marked as pending ("E") until the
    # solver updated them, which made the display flicker after each move
    lb = LightBoard()
    lb.move(1, 0, 2, 2)
    assert lb.getPiece(2, 0)["natures"] == major_piece_natures
    assert lb.getPiece(2, 7)["natures"] == major_piece_natures
    assert lb.getPiece(0, 1)["natures"] == ["P"]


@pytest.mark.parametrize(("color", "y1", "y2"), [(0, 6, 7), (1, 1, 0)])
def test_lightboard_promotion(color, y1, y2):
    natures = LightBoard.possibleNaturesFromMove(0, y1, 0, y2, color, ["P"])
    assert natures == ["Q", "R", "B", "N"]


def test_lightboard_no_promotion_backwards():
    assert LightBoard.possibleNaturesFromMove(0, 1, 0, 0, 0, ["P"]) == ["P"]


@pytest.mark.parametrize("protocol", [ChessClientProtocol, ChessServerProtocol])
@pytest.mark.parametrize("n", [1, 2, 3])
def test_split_messages(protocol, n):
    msgs = [{"type": "move", "description": [i, 1, i, 3]} for i in range(n)]
    data = "".join(json.dumps(m) for m in msgs).encode()
    split = protocol.split_messages(None, data)
    assert [json.loads(m) for m in split] == msgs


class FakePlayer:
    def __init__(self):
        self.sent = []
        self.state = None

    def sendMessage(self, msg):
        self.sent.append(msg)


def test_server_game():
    white, black = FakePlayer(), FakePlayer()
    game = Game(white, black, 0)
    assert white.sent == black.sent == [{"type": "status", "status": "ready"}]
    with pytest.raises(IllegalMove, match="does not belong"):
        game.move(4, 1, 4, 3, 1)
    game.move(4, 1, 4, 3, 0)
    assert game.validMovesCounter == 1
    with pytest.raises(IllegalMove, match="does not belong"):
        game.move(4, 3, 4, 4, 1)
    game.updateLightBoardTask()
    assert white.sent[-1]["type"] == "lightboard"
