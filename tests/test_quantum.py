"""Tests for the consistency checks on piece natures (integer program)."""

import pytest

from schroedingerchess.chess import ChessBoard, IllegalMove, major_piece_natures


def play(cb, moves):
    for move in moves:
        cb.move(*move, disp=False)


@pytest.fixture(params=["enumeration", "ilp"])
def cb(request):
    return ChessBoard(solver=request.param)


def test_initial_natures(cb):
    assert cb.all_legal_natures(cb.grid[0][0]) == major_piece_natures
    assert cb.all_legal_natures(cb.grid[0][1]) == ["P"]


def test_knight_nature(cb):
    play(cb, [(0, 0, 1, 2)])
    assert cb.all_legal_natures(cb.grid[1][2]) == ["N"]


def test_impossible_knight_move(cb):
    play(cb, [(0, 0, 1, 2), (0, 6, 0, 5)])
    with pytest.raises(IllegalMove):
        cb.move(1, 2, 1, 1, disp=False)


def test_too_many_knights(cb):
    play(cb, [(0, 0, 1, 2), (6, 6, 6, 5), (1, 0, 2, 2), (5, 6, 5, 5)])
    with pytest.raises(IllegalMove, match="any initial piece configuration"):
        cb.move(2, 0, 3, 2, disp=False)


def test_bishops_on_same_color(cb):
    # Pieces 2 and 4 start on dark squares and move along long diagonals,
    # so each of them is a bishop or the queen. Piece 6, also on a dark
    # square, can still be a bishop: both bishops may share a color.
    play(cb, [(1, 1, 1, 2), (0, 6, 0, 5), (2, 0, 0, 2), (1, 6, 1, 5)])
    play(cb, [(3, 1, 3, 2), (2, 6, 2, 5), (4, 0, 2, 2), (3, 6, 3, 5)])
    assert "B" in cb.all_legal_natures(cb.grid[6][0])
    # Once piece 6 also moves along a long diagonal, the three of them are
    # two bishops and the queen, so piece 5 can be neither
    play(cb, [(5, 1, 5, 2), (4, 6, 4, 5), (6, 0, 4, 2), (5, 6, 5, 5)])
    assert cb.all_legal_natures(cb.grid[5][0]) == ["K", "R", "N"]


def test_at_most_three_long_diagonal_movers(cb):
    play(cb, [(1, 1, 1, 2), (0, 6, 0, 5), (2, 0, 0, 2), (1, 6, 1, 5)])
    play(cb, [(3, 1, 3, 2), (2, 6, 2, 5), (4, 0, 2, 2), (3, 6, 3, 5)])
    play(cb, [(5, 1, 5, 2), (4, 6, 4, 5), (6, 0, 4, 2), (5, 6, 5, 5)])
    play(cb, [(6, 1, 6, 2), (6, 6, 6, 5)])
    with pytest.raises(IllegalMove, match="any initial piece configuration"):
        cb.move(5, 0, 7, 2, disp=False)


def test_cannot_leave_king_in_check(cb):
    # White piece 5 moves four squares diagonally, so it is a bishop or a
    # queen, and it attacks black piece 4 through the square (3, 6).
    play(cb, [(4, 1, 4, 2), (3, 6, 3, 5), (5, 0, 1, 4)])
    assert "K" in cb.all_legal_natures(cb.grid[4][7])
    # Black ignores the threat, so black piece 4 cannot be the king
    play(cb, [(0, 6, 0, 5)])
    assert "K" not in cb.all_legal_natures(cb.grid[4][7])


def test_test_move_does_not_mutate(cb):
    before = (cb.time, len(cb.moves), [row[:] for row in cb.grid])
    cb.test_move(4, 1, 4, 3)
    with pytest.raises(IllegalMove):
        cb.test_move(4, 1, 4, 5)
    assert (cb.time, len(cb.moves), cb.grid) == before


def test_promotion(cb):
    moves = [
        (1, 1, 1, 3), (6, 6, 6, 4),
        (1, 3, 1, 4), (6, 4, 6, 3),
        (1, 4, 1, 5), (6, 3, 6, 2),
        (1, 5, 0, 6), (6, 2, 7, 1),
        (0, 6, 1, 7),
    ]  # fmt: skip
    play(cb, moves)
    promoted = cb.grid[1][7]
    assert promoted.number == 9 + 8
    assert "P" not in cb.all_legal_natures(promoted)
    assert "K" not in cb.all_legal_natures(promoted)


def test_auto_move_falls_back_on_legal_move(cb, monkeypatch):
    # Regression: an illegal engine suggestion used to be returned anyway
    monkeypatch.setattr(cb, "engine_move_suggestions", lambda depth: [(4, 1, 4, 5)])
    move = cb.auto_move(intelligent=True)
    assert move != (4, 1, 4, 5)
    assert cb.test_move(*move)


def test_auto_move(cb):
    x1, y1, x2, y2 = cb.auto_move(intelligent=False)
    assert cb.test_move(x1, y1, x2, y2)
    x1, y1, x2, y2 = cb.auto_move(intelligent=True)
    assert cb.test_move(x1, y1, x2, y2)


def test_end_game(cb):
    assert cb.end_game() == "Legal moves still exist"
    # 16 pawn moves, plus 14 knight jumps since any major piece may be a knight
    assert len(cb.all_legal_moves()) == 30


def test_not_in_check_at_start(cb):
    # Regression: the integer program skipped squares without any attack,
    # so the king could be "in check" on them
    assert cb.explanation(check=True) is None
    assert cb.explanation(check=False) is not None


def test_unknown_solver():
    with pytest.raises(ValueError):
        ChessBoard(solver="magic")
