"""Minimal alpha-beta chess engine used to suggest moves for the computer.

The engine plays ordinary chess on a "guessed" board, where every piece is
given one plausible nature. Its suggestions are not guaranteed to be legal in
Schrödinger chess: they must be checked with
:meth:`schroedingerchess.chess.ChessBoard.test_move`.

Castling and en passant are ignored, pawns always promote to queens, and a
king may be left in check (the opponent then captures it, which the
evaluation punishes heavily).
"""

PIECE_VALUES = {"P": 100, "N": 300, "B": 320, "R": 500, "Q": 900, "K": 100_000}

_KING_STEPS = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0)]
_KNIGHT_STEPS = [(1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2)]
_ROOK_DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]
_BISHOP_DIRS = [(1, 1), (1, -1), (-1, 1), (-1, -1)]


def _on_board(x, y):
    return 0 <= x < 8 and 0 <= y < 8


def pseudo_legal_moves(board, color):
    """List the moves of ``color`` on ``board``, ignoring checks.

    :param board: Dictionary mapping squares ``(x, y)`` to ``(color, nature)``.
    :param color: 0 for white, 1 for black.
    :return: List of moves ``(x1, y1, x2, y2)``.
    """
    moves = []
    for (x, y), (c, n) in board.items():
        if c != color:
            continue
        if n == "P":
            d = 1 if color == 0 else -1
            if _on_board(x, y + d) and (x, y + d) not in board:
                moves.append((x, y, x, y + d))
                start = 1 if color == 0 else 6
                if y == start and (x, y + 2 * d) not in board:
                    moves.append((x, y, x, y + 2 * d))
            for dx in (-1, 1):
                target = board.get((x + dx, y + d))
                if target is not None and target[0] != color:
                    moves.append((x, y, x + dx, y + d))
            continue
        if n in ("K", "N"):
            for dx, dy in _KING_STEPS if n == "K" else _KNIGHT_STEPS:
                x2, y2 = x + dx, y + dy
                target = board.get((x2, y2))
                if _on_board(x2, y2) and (target is None or target[0] != color):
                    moves.append((x, y, x2, y2))
            continue
        dirs = {"R": _ROOK_DIRS, "B": _BISHOP_DIRS, "Q": _ROOK_DIRS + _BISHOP_DIRS}[n]
        for dx, dy in dirs:
            x2, y2 = x + dx, y + dy
            while _on_board(x2, y2):
                target = board.get((x2, y2))
                if target is None:
                    moves.append((x, y, x2, y2))
                elif target[0] != color:
                    moves.append((x, y, x2, y2))
                    break
                else:
                    break
                x2, y2 = x2 + dx, y2 + dy
    return moves


def make_move(board, move):
    """Return a new board where ``move`` has been played (promoting to queen)."""
    x1, y1, x2, y2 = move
    new_board = dict(board)
    c, n = new_board.pop((x1, y1))
    if n == "P" and y2 in (0, 7):
        n = "Q"
    new_board[(x2, y2)] = (c, n)
    return new_board


def evaluate(board, color):
    """Material balance from the point of view of ``color``, plus a small
    bonus for advanced pawns and centralized pieces."""
    score = 0
    for (x, y), (c, n) in board.items():
        value = PIECE_VALUES[n]
        if n == "P":
            value += 5 * (y - 1 if c == 0 else 6 - y)
        elif n != "K":
            value += 4 * (3 - max(abs(2 * x - 7), abs(2 * y - 7)) // 2)
        score += value if c == color else -value
    return score


def _negamax(board, color, depth, alpha, beta):
    if depth == 0:
        return evaluate(board, color)
    moves = pseudo_legal_moves(board, color)
    if not moves:
        return evaluate(board, color)
    # Captures first, most valuable victims first, for better pruning
    moves.sort(key=lambda m: -PIECE_VALUES[board[m[2:]][1]] if m[2:] in board else 0)
    best = -float("inf")
    for move in moves:
        target = board.get(move[2:])
        if target is not None and target[1] == "K":
            return PIECE_VALUES["K"]
        score = -_negamax(make_move(board, move), 1 - color, depth - 1, -beta, -alpha)
        best = max(best, score)
        alpha = max(alpha, score)
        if alpha >= beta:
            break
    return best


def rank_moves(board, color, depth=2):
    """Sort the moves of ``color`` from best to worst.

    :param board: Dictionary mapping squares ``(x, y)`` to ``(color, nature)``.
    :param color: 0 for white, 1 for black.
    :param depth: Search depth in plies (including the root move).
    :return: List of moves ``(x1, y1, x2, y2)``, best first.
    """
    scored = []
    for move in pseudo_legal_moves(board, color):
        new_board = make_move(board, move)
        score = -_negamax(new_board, 1 - color, depth - 1, -float("inf"), float("inf"))
        scored.append((score, move))
    scored.sort(key=lambda sm: -sm[0])
    return [move for _, move in scored]
