"""Compare the integer program and the enumeration on random games.

Run with ``uv run python benchmarks/solvers.py``. For each game length, the
script prints the median time (in milliseconds) of three tasks:

- ``check``: one consistency check of the history,
- ``moves``: listing all legal moves of the current player,
- ``natures``: computing the possible natures of every piece in play.
"""

import random
import statistics
import time

import numpy as np

from schroedingerchess.chess import ChessBoard

LENGTHS = [0, 10, 20, 40, 60]
SEEDS = range(5)
SOLVERS = ["ilp", "enumeration"]


def random_game(seed, length):
    """Moves of a random game, played until ``length`` or the end."""
    random.seed(seed)
    np.random.seed(seed)
    cb = ChessBoard()
    moves = []
    while cb.time < length:
        move = cb.auto_move(intelligent=random.random() < 0.5)
        cb.move(*move, disp=False)
        moves.append(move)
    return moves


def replay(moves, solver):
    cb = ChessBoard(solver=solver)
    for move in moves:
        cb.move(*move, disp=False)
    return cb


def timed(f, repeat=1):
    start = time.perf_counter()
    for _ in range(repeat):
        f()
    return 1000 * (time.perf_counter() - start) / repeat


def tasks(cb):
    pieces = [p for color in cb.pieces for p in color if p.position]
    return {
        "check": lambda: cb.explanation(),
        "moves": lambda: cb.all_legal_moves(),
        "natures": lambda: [cb.all_legal_natures(p, update=False) for p in pieces],
    }


def main():
    games = {seed: random_game(seed, max(LENGTHS)) for seed in SEEDS}
    results = {}
    for length in LENGTHS:
        for solver in SOLVERS:
            times = {}
            for seed, moves in games.items():
                cb = replay(moves[:length], solver)
                for name, task in tasks(cb).items():
                    repeat = 10 if name == "check" else 1
                    times.setdefault(name, []).append(timed(task, repeat))
            results[length, solver] = {
                k: statistics.median(v) for k, v in times.items()
            }

    print("| moves played | task | ILP (ms) | enumeration (ms) | speedup |")
    print("|---:|---|---:|---:|---:|")
    for length in LENGTHS:
        for name in ["check", "moves", "natures"]:
            ilp = results[length, "ilp"][name]
            enum = results[length, "enumeration"][name]
            print(f"| {length} | {name} | {ilp:.1f} | {enum:.1f} | {ilp / enum:.1f}x |")


if __name__ == "__main__":
    main()
