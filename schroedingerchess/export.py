"""Export games as text records or animations.

Text records follow the PGN format, with moves in long algebraic notation
(``e2e4``), since the usual notation (``Nf3``) needs the nature of the moving
piece, which is often unknown in this variant.
"""

import datetime
import os
import re

from .chess import ChessBoard, LightBoard, square_name


def move_name(move):
    """Long algebraic notation of a move ``(x1, y1, x2, y2)``, like ``"e2e4"``."""
    x1, y1, x2, y2 = move
    return square_name(x1, y1) + square_name(x2, y2)


def parse_move(name):
    """Coordinates ``(x1, y1, x2, y2)`` of a move in long algebraic notation."""
    if not re.fullmatch(r"[a-h][1-8][a-h][1-8]", name):
        raise ValueError(f"Not a move in long algebraic notation: {name!r}")
    return (
        ord(name[0]) - 97,
        int(name[1]) - 1,
        ord(name[2]) - 97,
        int(name[3]) - 1,
    )


def result_tag(outcome, player_to_move):
    """PGN result of an outcome of :meth:`ChessBoard.end_game`."""
    if outcome == "Current player checkmated":
        return "0-1" if player_to_move == 0 else "1-0"
    if outcome == "Stalemate" or outcome.startswith("Draw"):
        return "1/2-1/2"
    return "*"


def game_record(moves, outcome=None, date=None):
    """Text record of a game, in PGN format.

    :param moves: List of moves ``(x1, y1, x2, y2)``.
    :param outcome: Outcome of the game, as returned by
        :meth:`~schroedingerchess.chess.ChessBoard.end_game`, or None if unknown.
        It is written as a comment, and as the result when it is definite.
    :param date: Date of the game, today by default.
    """
    date = date or datetime.date.today()
    result = "*" if outcome is None else result_tag(outcome, len(moves) % 2)
    lines = [
        '[Event "Schrödinger chess game"]',
        '[Site "SchroedingerChess"]',
        f'[Date "{date:%Y.%m.%d}"]',
        '[Variant "Haft Schrödinger chess"]',
        f'[Result "{result}"]',
        "",
    ]
    tokens = []
    for t, move in enumerate(moves):
        if t % 2 == 0:
            tokens.append(f"{t // 2 + 1}.")
        tokens.append(move_name(move))
    if outcome is not None and outcome != "Legal moves still exist":
        tokens.append("{" + outcome + "}")
    tokens.append(result)
    # Wrap the movetext at 80 characters, as PGN recommends
    line = ""
    for token in tokens:
        if line and len(line) + 1 + len(token) > 80:
            lines.append(line)
            line = token
        else:
            line = f"{line} {token}" if line else token
    lines.append(line)
    return "\n".join(lines) + "\n"


def read_game_record(text):
    """Moves of a text record written by :func:`game_record`.

    :return: List of moves ``(x1, y1, x2, y2)``.
    """
    movetext = re.sub(r"\[.*?\]", " ", text)  # tags
    movetext = re.sub(r"\{.*?\}", " ", movetext, flags=re.S)  # comments
    moves = []
    for token in movetext.split():
        if re.fullmatch(r"\d+\.+", token) or token in ("1-0", "0-1", "1/2-1/2", "*"):
            continue
        moves.append(parse_move(token))
    return moves


def replay(moves, **kwargs):
    """Board after playing a list of moves.

    :raise IllegalMove: If one of the moves is illegal.
    """
    cb = ChessBoard(**kwargs)
    for move in moves:
        cb.move(*move, disp=False)
    return cb


def _light_board(cb):
    """Light board with the possible natures of every piece."""
    lb = LightBoard()
    natures = cb.all_possible_natures()
    for c in (0, 1):
        for i, piece in enumerate(cb.pieces[c]):
            lb.setPiece(i + 24 * c, c, piece.position, natures.get((c, i), []))
    return lb


def export_gif(moves, path, display, captions=None, durations=None, width=480):
    """Animate a game into a GIF file, with the drawing code of the game.

    :param moves: List of moves ``(x1, y1, x2, y2)``.
    :param path: Path of the GIF file.
    :param display: A :class:`~schroedingerchess.display.ChessDisplay` used to
        draw the frames. Its window is not modified, but it should be redrawn
        afterwards.
    :param captions: Optional function ``(t, cb) -> (title, subtitle)`` giving
        the caption of the frame after ``t`` half-moves.
    :param durations: Optional function ``t -> milliseconds``.
    :param width: Width of the animation, in pixels.
    """
    import pygame
    from PIL import Image

    from .display import BOARD, MUTED, TEXT

    def default_caption(t, cb):
        if t == 0:
            return "Schrödinger chess", "Starting position"
        player = "White" if t % 2 == 1 else "Black"
        title = f"{(t + 1) // 2}. {player}: {move_name(moves[t - 1])}"
        if t == len(moves):
            outcome = cb.end_game()
            if outcome != "Legal moves still exist":
                return title, outcome
        return title, ""

    captions = captions or default_caption
    durations = durations or (lambda t: 1500 if t in (0, len(moves)) else 600)
    caption_height = 70
    saved = (display.state, display.last_move, display.selectedBox, display.flip)
    display.state, display.selectedBox, display.flip = "PLAYING", None, False
    scale = display.canvas.scale
    frames = []
    try:
        cb = ChessBoard()
        for t in range(len(moves) + 1):
            if t > 0:
                cb.move(*moves[t - 1], disp=False)
                display.last_move = moves[t - 1]
            else:
                display.last_move = (-1, -1, -1, -1)
            display.canvas.fill((32, 34, 39))
            display._draw_board(_light_board(cb))
            size = (display.canvas.px(BOARD), display.canvas.px(BOARD + caption_height))
            surface = pygame.Surface(size)
            surface.fill((32, 34, 39))
            surface.blit(display.screen, (0, 0), (0, 0, size[0], size[0]))
            title, subtitle = captions(t, cb)
            for text, font, color, y in [
                (title, display.font_bold, TEXT, BOARD + 12),
                (subtitle, display.small_font, MUTED, BOARD + 40),
            ]:
                rendered = font.render(text, color)
                center = (size[0] // 2, round(y * scale))
                surface.blit(rendered, rendered.get_rect(midtop=center))
            image = Image.frombytes("RGB", size, pygame.image.tobytes(surface, "RGB"))
            height = round(width * size[1] / size[0])
            image = image.resize((width, height), Image.LANCZOS)
            frames.append(image.quantize(colors=128, method=Image.Quantize.MEDIANCUT))
    finally:
        display.state, display.last_move, display.selectedBox, display.flip = saved
    frames[0].save(
        path,
        save_all=True,
        append_images=frames[1:],
        duration=[durations(t) for t in range(len(frames))],
        loop=0,
        optimize=True,
    )
    return path


def export_folder():
    """Folder where the game saves its exports: Downloads, or the current one."""
    downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    return downloads if os.path.isdir(downloads) else os.getcwd()


def export_name(extension, folder=None):
    """Path of a new export file, named after the current date and time."""
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    return os.path.join(
        folder or export_folder(), f"schroedinger-chess-{stamp}.{extension}"
    )
