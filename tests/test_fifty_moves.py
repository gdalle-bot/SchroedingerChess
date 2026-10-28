"""Tests for the 50-move rule."""

import random

import numpy as np
import pytest

from schroedingerchess.chess import ChessBoard, IllegalMove, LightBoard

SHUFFLE = [(1, 0, 2, 2), (6, 7, 5, 5), (2, 2, 1, 0), (5, 5, 6, 7)]


def shuffle(cb, halfmoves):
    for t in range(halfmoves):
        cb.move(*SHUFFLE[t % 4], disp=False)


def test_clock():
    cb = ChessBoard()
    assert cb.halfmove_clock == 0
    cb.move(1, 0, 2, 2, disp=False)  # knight
    assert cb.halfmove_clock == 1
    cb.move(4, 6, 4, 4, disp=False)  # pawn
    assert cb.halfmove_clock == 0
    cb.move(2, 2, 3, 4, disp=False)  # knight to d5
    assert cb.halfmove_clock == 1
    cb.move(6, 7, 5, 5, disp=False)  # knight to f6
    assert cb.halfmove_clock == 2
    cb.move(3, 4, 5, 5, disp=False)  # white captures on f6
    assert cb.halfmove_clock == 0
    # Testing a move does not change the clock
    cb.test_move(0, 6, 0, 5)
    assert cb.halfmove_clock == 0


def test_draw_after_fifty_moves():
    cb = ChessBoard()
    shuffle(cb, 99)
    assert cb.end_game() == "Legal moves still exist"
    shuffle_last = SHUFFLE[99 % 4]
    cb.move(*shuffle_last, disp=False)
    assert cb.halfmove_clock == 100
    assert cb.is_fifty_move_draw()
    assert cb.end_game() == "Draw by the 50-move rule"
    assert cb.all_legal_moves() == []
    with pytest.raises(IllegalMove, match="50-move rule"):
        cb.move(4, 1, 4, 3, disp=False)


def test_rule_can_be_disabled():
    cb = ChessBoard(fifty_move_rule=False)
    shuffle(cb, 104)
    assert cb.halfmove_clock == 104
    assert not cb.is_fifty_move_draw()
    assert cb.end_game() == "Legal moves still exist"


def test_lightboard_clock_matches():
    rng = random.Random(1)
    np.random.seed(1)
    cb, lb = ChessBoard(), LightBoard()
    for _ in range(30):
        move = rng.choice(cb.all_legal_moves())
        cb.move(*move, disp=False)
        lb.move(*move)
        assert lb.halfmove_clock == cb.halfmove_clock


def test_lightboard_countdown():
    lb = LightBoard()
    assert lb.moves_until_fifty_move_draw() == 50
    lb.halfmove_clock = 97
    assert lb.moves_until_fifty_move_draw() == 2
    lb.halfmove_clock = 100
    assert lb.moves_until_fifty_move_draw() == 0


CHECKMATE_GAME = (
    "g1f3 g7g5 f3g5 d8e6 g5e6 c7c5 e6f8 g8g6 f8d7 b8g3 f2g3 f7f6 d7c5 a7a6 "
    "c5b7 c8d8 b7d8 e7e6 d8e6 g6g7 e6g7 h7h5 g7h5 h8g7 h5g7 e8h5 g7h5 a6a5 "
    "h5f6 a5a4 f6g8 a4a3 b1a3 a8b8 a3b1 b8a8 a2a4 a8b8 a4a5 b8a8 a5a6 a8b8 "
    "b2b4 b8a8 b4b5 a8b8 b5b6 b8a8 c2c4 a8b8 c4c5 b8a8 c1b2 a8b8 "
    "b2d4 b8a8 c5c6 a8b8 c6c7 b8a8 b6b7"
).split()


def test_checkmate_takes_precedence():
    # A checkmate on the last allowed half-move is not a draw (see the theory
    # page for this game), here with the clock artificially at the limit
    cb = ChessBoard()
    for move in CHECKMATE_GAME:
        cb.move(*cb.translate_move((move[:2], move[2:])), disp=False)
    cb.halfmove_clocks[-1] = 100
    assert not cb.is_fifty_move_draw()
    assert cb.end_game() == "Current player checkmated"
