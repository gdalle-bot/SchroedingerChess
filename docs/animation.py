"""Render the game of the theory page that ends with an undetermined result.

Run ``uv run --group docs python docs/animation.py`` to create
``docs/_static/undetermined.gif``, which is committed since rendering takes
a minute.
"""

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
os.environ["SCHROEDINGERCHESS_HIGHDPI"] = "0"

import pygame  # noqa: E402
from PIL import Image  # noqa: E402

from schroedingerchess.chess import ChessBoard, LightBoard, square_name  # noqa: E402
from schroedingerchess.display import BOARD, MUTED, TEXT, ChessDisplay  # noqa: E402
from schroedingerchess.game_engines import GameEngine  # noqa: E402

GAME = (
    "g1f3 g7g5 f3g5 d8e6 g5e6 c7c5 e6f8 g8g6 f8d7 b8g3 f2g3 f7f6 d7c5 a7a6 "
    "c5b7 c8d8 b7d8 e7e6 d8e6 g6g7 e6g7 h7h5 g7h5 h8g7 h5g7 e8h5 g7h5 a6a5 "
    "h5f6 a5a4 f6g8 a4a3 b1a3 a8b8 a3b1 b8a8 a2a4 a8b8 a4a5 b8a8 a5a6 a8b8 "
    "b2b4 b8a8 b4b5 a8b8 b5b6 b8a8 c2c4 a8b8 c4c5 b8a8 c1b2 a8b8 "
    "b2g7 b8a8 c5c6 a8b8 c6c7 b8a8 g7f8"
).split()

CAPTION = 70  # height of the caption below the board, in points
SIZE = 480  # width of the animation, in pixels


def light_board(cb):
    """Light board with the possible natures of every piece, as in the game."""
    lb = LightBoard()
    for c in (0, 1):
        for i, piece in enumerate(cb.pieces[c]):
            natures = cb.all_legal_natures(piece, update=False)
            lb.setPiece(i + 24 * c, piece.color, piece.position, natures)
    return lb


def frame(display, cb, caption, subcaption):
    """Draw the board and a caption, and return them as an image."""
    display._draw_board(light_board(cb))
    surface = pygame.Surface((BOARD, BOARD + CAPTION))
    surface.fill((32, 34, 39))
    surface.blit(display.screen, (0, 0), (0, 0, BOARD, BOARD))
    for text, font, color, y in [
        (caption, display.font_bold, TEXT, BOARD + 12),
        (subcaption, display.small_font, MUTED, BOARD + 40),
    ]:
        rendered = font.render(text, color)
        surface.blit(rendered, rendered.get_rect(midtop=(BOARD // 2, y)))
    image = Image.frombytes(
        "RGB", surface.get_size(), pygame.image.tobytes(surface, "RGB")
    )
    height = round(SIZE * surface.get_height() / surface.get_width())
    return image.resize((SIZE, height), Image.LANCZOS)


def make_animation(path):
    """Render the game into an animated GIF at ``path``."""
    engine = GameEngine()
    engine.lightBoard = LightBoard()
    display = ChessDisplay(engine)
    display.state = "PLAYING"
    cb = ChessBoard()
    frames = [frame(display, cb, "An undetermined ending", "Starting position")]
    durations = [1500]
    for t, move in enumerate(GAME):
        x1, y1, x2, y2 = cb.translate_move((move[:2], move[2:]))
        cb.move(x1, y1, x2, y2, disp=False)
        display.setLastMove(x1, y1, x2, y2)
        player = "White" if t % 2 == 0 else "Black"
        caption = f"{t // 2 + 1}. {player}: {square_name(x1, y1)}-{square_name(x2, y2)}"
        if t < 33:
            subcaption = "White captures every black piece but the one on a8"
        elif t < len(GAME) - 1:
            subcaption = "The piece from c1 only moves diagonally: queen or bishop?"
        else:
            subcaption = "Black cannot move: checkmate or stalemate?"
        frames.append(frame(display, cb, caption, subcaption))
        durations.append(350 if t < 33 else 700)
    shares = cb.outcome_shares()
    frames.append(
        frame(
            display,
            cb,
            f"Checkmate in {100 * shares['checkmate']:.0f}% of the arrangements",
            f"(the piece on f8 is the queen), stalemate in "
            f"{100 * shares['stalemate']:.0f}% (it is a bishop)",
        )
    )
    durations[-1] = 1500
    durations.append(5000)
    frames = [f.quantize(colors=128, method=Image.Quantize.MEDIANCUT) for f in frames]
    frames[0].save(
        path,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=True,
    )
    pygame.quit()


if __name__ == "__main__":
    out = (
        sys.argv[1]
        if len(sys.argv) > 1
        else os.path.join(os.path.dirname(__file__), "_static", "undetermined.gif")
    )
    make_animation(out)
    print(out, os.path.getsize(out) // 1024, "KiB")
