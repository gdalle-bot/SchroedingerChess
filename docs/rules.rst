Rules
=====

Haft Schrödinger chess is a chess variant
`introduced by Antumbra Station <http://antumbrastation.com/schroedinger-chess/2017/11/28/introduction-to-haft-schroedinger-chess.html>`_.
Like ordinary chess, it is deterministic and has no hidden information.

Principle
---------

At the start, the eight back-rank pieces of each player have no fixed nature (king, queen, rook, bishop or knight).
They acquire one through the moves they make, and through the constraints linking them:

- A piece that moves along a long straight line is a rook or the queen. If it later moves along a diagonal, it must be the queen.
- If three pieces of the same player have moved like rooks, one of them is the queen, so the remaining pieces cannot be the queen.
- If a piece threatens a square, the opponent's piece standing there cannot be the king, unless the threat comes from a nature that the attacker does not have.

Formally, a game of *scramble chess* is a game of ordinary chess (without castling)
where each player is free to arrange their back-rank pieces before the first move.
A move of Haft Schrödinger chess is legal if there exists a starting arrangement of scramble chess
in which the whole sequence of moves played so far, including this one, is legal.

Differences with the original rules
-----------------------------------

This implementation departs from the original rules in a few ways:

- Castling and en passant are not allowed.
- Each player must have one bishop on light squares and one bishop on dark squares, whereas the original scramble chess arrangements allow two bishops of the same square color.
- A promoted pawn becomes a new piece of undetermined nature (anything but a king), which is constrained by its subsequent moves only. In particular, promoting does not consume the "budget" of queens, rooks, bishops and knights.
- The game ends when the player to move has no legal move, which is equivalent to the original end condition (see :doc:`theory`).
  However, the original rules do not say who wins when some compatible arrangements give a checkmate and others a stalemate:
  :meth:`~schroedingerchess.chess.ChessBoard.end_game` then reports an unclear result.

How legality is checked
-----------------------

Checking whether a move is legal amounts to deciding whether a set of constraints on the piece natures is satisfiable.
This is done with an integer linear program, described in :doc:`formulation`.
