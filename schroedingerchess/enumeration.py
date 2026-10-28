"""Consistency check by enumeration, as an alternative to the integer program.

Each player's back-rank pieces form one of the 2880 arrangements of RNBQKBNR
with bishops on opposite colors (see :doc:`/formulation`). Promoted pieces
can be a queen, rook, bishop or knight. We enumerate the arrangements of each
player that are compatible with the moves of their own pieces, and then
handle the check constraints, which are the only ones coupling both players.

The check constraints of an attacker only depend on the attacker's
arrangement and on which piece is the defender's king. Hence, instead of
testing all pairs of arrangements, we compute for each arrangement the set of
enemy kings it allows, and combine both players through the 8 x 8 possible
pairs of kings.
"""

import itertools

import numpy as np

NATURES = ["K", "Q", "R", "B", "N"]
PROMOTED_NATURES = [1, 2, 3, 4]  # indices of Q, R, B, N
MAJOR = list(range(8))
PROMOTED = list(range(16, 24))
PAWNS = list(range(8, 16))

#: Maximum number of configurations per player before giving up. Each promoted
#: piece multiplies the number of configurations by up to 4.
MAX_CONFIGURATIONS = 200_000


class TooManyConfigurations(Exception):
    """Raised when enumerating would require too much time and memory."""


def _arrangements():
    """All arrangements of the major pieces, as an array of nature indices."""
    result = set()
    for perm in itertools.permutations([0, 1, 2, 2, 3, 3, 4, 4]):
        bishops = [i for i in range(8) if perm[i] == 3]
        if bishops[0] % 2 != bishops[1] % 2:
            result.add(perm)
    return np.array(sorted(result), dtype=np.int8)


ARRANGEMENTS = _arrangements()


def _configurations(cb, c, active_promoted):
    """Arrangements of color ``c`` compatible with the moves of its own pieces.

    :return: Array of shape ``(n, 8 + len(active_promoted))`` of nature indices.
    """
    forbidden = {i: set(cb.pieces[c][i].forbidden_natures) for i in MAJOR + PROMOTED}
    for t in range(cb.time):
        cc, i, natures = cb.nature_eliminations[t]
        if cc == c and i in forbidden:
            forbidden[i].update(natures)

    configs = ARRANGEMENTS
    for i in MAJOR:
        if forbidden[i]:
            bad = [NATURES.index(n) for n in forbidden[i]]
            configs = configs[~np.isin(configs[:, i], bad)]
    allowed_promoted = []
    size = len(configs)
    for i in active_promoted:
        allowed = [n for n in PROMOTED_NATURES if NATURES[n] not in forbidden[i]]
        allowed_promoted.append(allowed)
        size *= len(allowed)
    if size > MAX_CONFIGURATIONS:
        raise TooManyConfigurations(f"{size} configurations for color {c}")
    for allowed in allowed_promoted:
        if not allowed or len(configs) == 0:
            return np.zeros((0, configs.shape[1] + 1), dtype=np.int8)
        n_allowed = len(allowed)
        configs = np.hstack(
            [
                np.repeat(configs, n_allowed, axis=0),
                np.tile(np.array(allowed, dtype=np.int8), len(configs))[:, None],
            ]
        )
    # Promoted pieces cannot be kings, but other constraints on unused
    # promoted pieces are always satisfiable
    for i in PROMOTED:
        if i not in active_promoted and forbidden[i] >= set(NATURES[1:]):
            return np.zeros((0, configs.shape[1]), dtype=np.int8)
    return configs


def _allowed_kings(cb, c, configs, pieces, check):
    """Which enemy kings each configuration of the attacker ``c`` allows.

    :return: Boolean array of shape ``(len(configs), 8)``.
    """
    d = 1 - c
    T = cb.time
    ok = np.ones((len(configs), 8), dtype=bool)
    if len(configs) == 0:
        return ok
    rows = np.arange(len(pieces))
    # Times when the defender just moved, and must not be in check
    times = [(t, False) for t in range(1, T + 1) if t % 2 == c]
    # Optional constraint on the current position, for the end of the game
    if check is not None and T % 2 == d:
        times.append((T, check))
    for t, attacked in times:
        positions, attacks = cb.positions[t], cb.attacks[t]
        squares = np.argmax(positions[:, d, :8], axis=0)
        on_board = positions[squares, d, range(8)] > 0.5
        for k in np.flatnonzero(~on_board):
            if attacked:
                ok[:, k] = False
        kings = np.flatnonzero(on_board)
        s = squares[kings]
        pawn_danger = attacks[s][:, c, PAWNS, -1].sum(axis=1)
        matrices = attacks[s][:, c][:, pieces, :]  # (kings, pieces, natures)
        if not attacked:
            # Kings attacked by a pawn are impossible for every configuration
            ok[:, kings[pawn_danger > 0.5]] = False
            # Kings that no piece attacks are always possible
            relevant = (pawn_danger < 0.5) & (
                matrices.reshape(len(kings), -1).max(axis=1) > 0.5
            )
            kings, matrices, pawn_danger = (
                kings[relevant],
                matrices[relevant],
                pawn_danger[relevant],
            )
        if len(kings) == 0:
            continue
        # danger[k, cfg] = sum over pieces p of matrices[k, p, configs[cfg, p]]
        danger = matrices[:, rows[None, :], configs].sum(axis=2) + pawn_danger[:, None]
        ok[:, kings] &= ((danger > 0.5) if attacked else (danger < 0.5)).T
    return ok


def explanation(cb, check=None):
    """Find natures of all pieces explaining the history of the board.

    This solves the same problem as
    :meth:`~schroedingerchess.chess.ChessBoard.quantum_explanation`.

    :param cb: A :class:`~schroedingerchess.chess.ChessBoard`.
    :param check: If True (resp. False), also require the current player to be
        in check (resp. not in check).
    :return: Dictionary mapping ``(color, number)`` to a nature for the major
        and promoted pieces in play, or None if there is no explanation.
    :raise TooManyConfigurations: If there are too many promoted pieces.
    """
    active = []
    for c in (0, 1):
        # Promoted pieces get a position (False once captured) when they appear
        promoted = [i for i in PROMOTED if cb.pieces[c][i].position is not None]
        active.append(promoted)

    configs = [_configurations(cb, c, active[c]) for c in (0, 1)]
    if any(len(cfg) == 0 for cfg in configs):
        return None
    pieces = [MAJOR + active[c] for c in (0, 1)]
    ok = [_allowed_kings(cb, c, configs[c], pieces[c], check) for c in (0, 1)]
    kings = [np.argmax(configs[c][:, :8] == 0, axis=1) for c in (0, 1)]

    # possible[c][k_own, k_enemy]: some configuration of c has its king on
    # piece k_own and allows the enemy king to be piece k_enemy
    possible = []
    for c in (0, 1):
        table = np.zeros((8, 8), dtype=bool)
        for k in range(8):
            mask = kings[c] == k
            if mask.any():
                table[k] = ok[c][mask].any(axis=0)
        possible.append(table)
    pairs = np.argwhere(possible[0] & possible[1].T)  # (white king, black king)
    if len(pairs) == 0:
        return None

    kw, kb = pairs[0]
    own_king, enemy_king = [kw, kb], [kb, kw]
    solution = {}
    for c in (0, 1):
        mask = (kings[c] == own_king[c]) & ok[c][:, enemy_king[c]]
        config = configs[c][np.argmax(mask)]
        for j, i in enumerate(pieces[c]):
            solution[(c, i)] = NATURES[config[j]]
    return solution
