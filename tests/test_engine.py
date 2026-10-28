"""Tests for the alpha-beta engine on ordinary chess boards."""

from schroedingerchess import engine
from schroedingerchess.chess import ChessBoard

START = ChessBoard().guessed_board()


def test_guessed_board():
    assert START[(4, 0)] == (0, "K")
    assert START[(3, 7)] == (1, "Q")
    assert START[(0, 6)] == (1, "P")
    assert len(START) == 32


def test_initial_moves():
    assert len(engine.pseudo_legal_moves(START, 0)) == 20
    assert len(engine.pseudo_legal_moves(START, 1)) == 20


def test_sliding_pieces():
    board = {(0, 0): (0, "R"), (0, 3): (1, "P"), (3, 3): (0, "B"), (4, 4): (0, "N")}
    moves = engine.pseudo_legal_moves(board, 0)
    rook = {m[2:] for m in moves if m[:2] == (0, 0)}
    assert rook == {(0, 1), (0, 2), (0, 3)} | {(x, 0) for x in range(1, 8)}
    bishop = {m[2:] for m in moves if m[:2] == (3, 3)}
    assert (4, 4) not in bishop and (2, 2) in bishop and (0, 6) in bishop


def test_promotion():
    board = engine.make_move({(0, 6): (0, "P")}, (0, 6, 0, 7))
    assert board == {(0, 7): (0, "Q")}


def test_captures_hanging_queen():
    board = {(0, 0): (0, "K"), (7, 7): (1, "K"), (3, 3): (0, "R"), (3, 6): (1, "Q")}
    assert engine.rank_moves(board, 0)[0] == (3, 3, 3, 6)


def test_avoids_losing_queen():
    board = {(0, 0): (0, "K"), (7, 7): (1, "K"), (4, 4): (0, "Q"), (3, 6): (1, "P")}
    best = engine.rank_moves(board, 0)[0]
    assert engine.make_move(board, best).get((2, 5)) is None  # not into pawn range
    assert best[2:] not in {(2, 5), (4, 5)}


def test_black_moves():
    board = {(0, 0): (0, "K"), (7, 7): (1, "K"), (3, 1): (0, "Q"), (3, 6): (1, "R")}
    assert engine.rank_moves(board, 1)[0] == (3, 6, 3, 1)
