"""Render the game of the theory page that ends with an undetermined result.

Run ``uv run python docs/animation.py`` to create ``docs/_static/undetermined.gif``,
which is committed so that building the docs does not depend on it.
"""

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
os.environ["SCHROEDINGERCHESS_HIGHDPI"] = "0"

from schroedingerchess import export  # noqa: E402
from schroedingerchess.chess import LightBoard  # noqa: E402
from schroedingerchess.display import ChessDisplay  # noqa: E402
from schroedingerchess.game_engines import GameEngine  # noqa: E402

GAME = (
    "g1f3 g7g5 f3g5 d8e6 g5e6 c7c5 e6f8 g8g6 f8d7 b8g3 f2g3 f7f6 d7c5 a7a6 "
    "c5b7 c8d8 b7d8 e7e6 d8e6 g6g7 e6g7 h7h5 g7h5 h8g7 h5g7 e8h5 g7h5 a6a5 "
    "h5f6 a5a4 f6g8 a4a3 b1a3 a8b8 a3b1 b8a8 a2a4 a8b8 a4a5 b8a8 a5a6 a8b8 "
    "b2b4 b8a8 b4b5 a8b8 b5b6 b8a8 c2c4 a8b8 c4c5 b8a8 c1b2 a8b8 "
    "b2g7 b8a8 c5c6 a8b8 c6c7 b8a8 g7f8"
).split()
MOVES = [export.parse_move(move) for move in GAME]


def caption(t, cb):
    """Title and explanation of the frame after ``t`` half-moves."""
    if t == 0:
        return "An undetermined ending", "Starting position"
    player = "White" if t % 2 == 1 else "Black"
    title = f"{(t + 1) // 2}. {player}: {GAME[t - 1]}"
    if t <= 33:
        return title, "White captures every black piece but the one on a8"
    if t < len(GAME):
        return title, "The piece from c1 only moves diagonally: queen or bishop?"
    shares = cb.outcome_shares()
    return (
        f"Checkmate in {100 * shares['checkmate']:.0f}% of the arrangements",
        f"(the piece on f8 is the queen), stalemate in "
        f"{100 * shares['stalemate']:.0f}% (it is a bishop)",
    )


def duration(t):
    """Duration of the frame after ``t`` half-moves, in milliseconds."""
    if t == 0:
        return 1500
    if t == len(GAME):
        return 6000
    return 350 if t <= 33 else 800


if __name__ == "__main__":
    out = (
        sys.argv[1]
        if len(sys.argv) > 1
        else os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "_static", "undetermined.gif"
        )
    )
    engine = GameEngine()
    engine.lightBoard = LightBoard()
    display = ChessDisplay(engine)
    export.export_gif(MOVES, out, display, captions=caption, durations=duration)
    print(out, os.path.getsize(out) // 1024, "KiB")
