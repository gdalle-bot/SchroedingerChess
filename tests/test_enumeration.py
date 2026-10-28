"""Tests for the enumeration solver, compared with the integer program."""

import itertools
import random

import numpy as np
import pytest

from schroedingerchess import enumeration
from schroedingerchess.chess import ChessBoard


def test_arrangements():
    arrangements = enumeration.ARRANGEMENTS
    assert arrangements.shape == (5040, 8)
    assert len({tuple(a) for a in arrangements}) == 5040
    for a in arrangements:
        assert sorted(a) == [0, 1, 2, 2, 3, 3, 4, 4]


def same_answer(cb, check=None):
    ilp = cb.quantum_explanation(check=check)[1] == 1
    return ilp == (enumeration.explanation(cb, check=check) is not None)


def test_random_game_matches_ilp():
    rng = random.Random(0)
    np.random.seed(0)
    cb = ChessBoard()
    for _ in range(16):
        candidates = [
            move
            for move in itertools.product(range(8), repeat=4)
            if cb.trivial_test_move(*move) is None
        ]
        legal = []
        for move in rng.sample(candidates, min(10, len(candidates))):
            piece, target = cb.grid[move[0]][move[1]], cb.grid[move[2]][move[3]]
            cb.add_move_to_history(*move, piece, target)
            assert same_answer(cb)
            if enumeration.explanation(cb) is not None:
                legal.append(move)
            cb.delete_move_from_history(*move, piece, target)
        assert same_answer(cb, check=True)
        assert same_answer(cb, check=False)
        cb.move(*(rng.choice(legal) if legal else cb.auto_move(False)), disp=False)


def test_solution_is_consistent():
    cb = ChessBoard()
    for move in [(1, 0, 2, 2), (4, 6, 4, 4), (6, 0, 5, 2)]:
        cb.move(*move, disp=False)
    solution = enumeration.explanation(cb)
    assert solution[(0, 1)] == "N"
    assert solution[(0, 6)] == "N"
    for c in (0, 1):
        natures = sorted(solution[(c, i)] for i in range(8))
        assert natures == sorted("RNBQKBNR")


def test_fallback_on_ilp(monkeypatch):
    monkeypatch.setattr(enumeration, "MAX_CONFIGURATIONS", 0)
    cb = ChessBoard()
    with pytest.raises(enumeration.TooManyConfigurations):
        enumeration.explanation(cb)
    cb.move(1, 0, 2, 2, disp=False)  # uses the integer program
    assert cb.all_legal_natures(cb.grid[2][2]) == ["N"]


def test_count_at_start():
    assert ChessBoard().count_explanations() == 5040**2


def test_count_partitions():
    rng = random.Random(3)
    np.random.seed(3)
    cb = ChessBoard()
    for _ in range(12):
        cb.move(*rng.choice(cb.all_legal_moves()), disp=False)
        total = cb.count_explanations()
        assert total > 0
        # In check or not
        assert total == cb.count_explanations(True) + cb.count_explanations(False)
        # Partition by the nature of one piece
        piece = cb.pieces[cb.time % 2][rng.randrange(8)]
        by_nature = 0
        for n in "KQRBN":
            piece.forbidden_natures = [m for m in "KQRBN" if m != n]
            by_nature += cb.count_explanations()
        piece.forbidden_natures = []
        assert by_nature == total


def test_count_matches_explanation():
    cb = ChessBoard()
    cb.move(1, 0, 2, 2, disp=False)
    piece = cb.pieces[0][1]
    for n in "KQRBN":
        piece.forbidden_natures = [m for m in "KQRBN" if m != n]
        assert (cb.count_explanations() > 0) == (cb.explanation() is not None)
    piece.forbidden_natures = []
    # The knight is determined, and the other 7 pieces of white are free
    assert cb.count_explanations() == (5040 * 2 // 8) * 5040


def test_possible_natures_at_once():
    rng = random.Random(5)
    np.random.seed(5)
    cb = ChessBoard()
    for _ in range(14):
        cb.move(*rng.choice(cb.all_legal_moves()), disp=False)
        at_once = cb.all_possible_natures()
        for (c, i), natures in at_once.items():
            assert natures == cb.all_legal_natures(cb.pieces[c][i], update=False)
