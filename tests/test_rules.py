"""Tests for the move geometry, independent of piece natures."""

import pytest

from schroedingerchess.chess import ChessBoard


@pytest.fixture
def cb():
    return ChessBoard()


def test_initial_grid(cb):
    for x in range(8):
        assert cb.grid[x][0].color == 0 and cb.grid[x][0].number == x
        assert cb.grid[x][1].color == 0 and cb.grid[x][1].number == x + 8
        assert cb.grid[x][6].color == 1 and cb.grid[x][6].number == x + 8
        assert cb.grid[x][7].color == 1 and cb.grid[x][7].number == x
        for y in range(2, 6):
            assert cb.grid[x][y] is None


def test_square_coord_roundtrip(cb):
    for s in range(64):
        assert cb.get_square(*cb.get_coord(s)) == s


@pytest.mark.parametrize(
    ("move", "exists"),
    [
        ((0, 0, 0, 7), True),  # vertical
        ((0, 0, 7, 0), True),  # horizontal
        ((0, 0, 7, 7), True),  # diagonal
        ((1, 0, 2, 2), True),  # knight
        ((1, 0, 3, 1), True),  # knight
        ((0, 0, 0, 0), False),  # null move
        ((0, 0, 3, 1), False),
        ((0, 0, 2, 5), False),
    ],
)
def test_move_exists(cb, move, exists):
    assert cb.move_exists(*move) == exists


@pytest.mark.parametrize(
    ("nature", "move", "possible"),
    [
        ("K", (4, 4, 5, 5), True),
        ("K", (4, 4, 4, 6), False),
        ("Q", (4, 4, 4, 7), True),
        ("Q", (4, 4, 7, 7), True),
        ("Q", (4, 4, 5, 6), False),
        ("R", (4, 4, 0, 4), True),
        ("R", (4, 4, 5, 5), False),
        ("B", (4, 4, 1, 1), True),
        ("B", (4, 4, 4, 5), False),
        ("N", (4, 4, 6, 5), True),
        ("N", (4, 4, 6, 6), False),
    ],
)
def test_possible_move(cb, nature, move, possible):
    assert cb.possible_move(*move, nature, 0) == possible


def test_pawn_moves(cb):
    # White pawns go up, black pawns go down, double step only from start
    assert cb.pawn_could_reach(4, 1, 4, 3, 0)
    assert not cb.pawn_could_reach(4, 2, 4, 4, 0)
    assert not cb.pawn_could_reach(4, 1, 4, 0, 0)
    assert cb.pawn_could_reach(4, 6, 4, 4, 1)
    assert not cb.pawn_could_reach(4, 6, 4, 7, 1)
    assert cb.pawn_could_take(4, 3, 5, 4, 0)
    assert not cb.pawn_could_take(4, 3, 5, 2, 0)
    assert cb.pawn_could_take(4, 4, 3, 3, 1)


def test_free_trajectory(cb):
    assert cb.free_trajectory(1, 0, 2, 2)  # knights jump
    assert not cb.free_trajectory(0, 0, 0, 3)  # blocked by the pawn
    assert cb.free_trajectory(0, 1, 0, 5)
    assert cb.free_trajectory(0, 1, 0, 6)  # target square is not checked


@pytest.mark.parametrize(
    ("move", "error"),
    [
        ((0, 0, 0, 8), "outside of the board"),
        ((4, 4, 4, 5), "move the void"),
        ((4, 6, 4, 5), "out of turn"),
        ((0, 0, 1, 0), "eat a friend"),
        ((1, 0, 4, 2), "doesn't exist in chess"),
        ((0, 0, 0, 3), "through other pieces"),
        ((4, 1, 4, 4), "illegal pawn move"),
        ((4, 1, 5, 2), "illegal pawn move"),
    ],
)
def test_trivial_errors(cb, move, error):
    assert error in cb.trivial_test_move(*move)


def test_trivial_ok(cb):
    assert cb.trivial_test_move(4, 1, 4, 3) is None
    assert cb.trivial_test_move(1, 0, 2, 2) is None


def test_translate_move(cb):
    assert cb.translate_move((4, 1, 4, 3)) == ("e2", "e4")
    assert cb.translate_move(("e2", "e4")) == (4, 1, 4, 3)
