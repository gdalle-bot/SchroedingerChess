Theoretical results
===================

This page collects a few properties of Haft Schrödinger chess, as implemented here.
The main questions are: does a game always end, and when it ends, do we know who won?
Short answers: a game does not have to end, unless a move-counting rule is added;
and when it ends, the result can be undetermined between a win and a draw.

The examples below are executed as tests, with both the enumeration and the integer program.

Setting
-------

An *arrangement* :math:`A` assigns a nature to every major piece of both players, as a permutation of RNBQKBNR,
and a nature (Q, R, B or N) to every piece obtained by promotion.
Given an arrangement, the game is ordinary chess without castling or en passant: we call it *scramble chess* under :math:`A`.

A *history* :math:`H` is a sequence of moves :math:`(m_1, \dots, m_T)`, and :math:`H \cdot m` is the history extended by a move :math:`m`.
We denote by :math:`\mathrm{Cons}(H)` the set of arrangements under which every move of :math:`H` is legal in scramble chess.
By definition, :math:`H` is a legal history of Haft Schrödinger chess if :math:`\mathrm{Cons}(H) \neq \emptyset`,
and :math:`m` is a legal move after :math:`H` if :math:`\mathrm{Cons}(H \cdot m) \neq \emptyset`.
This is exactly what the :doc:`formulation` checks.

Legal moves
-----------

**Proposition 1 (ordinary chess is included).**
Every legal game of ordinary chess without castling or en passant is a legal history of Haft Schrödinger chess.

*Proof.* The standard arrangement RNBQKBNR belongs to :math:`\mathrm{Cons}(H)`. :math:`\square`

The converse is false: on the first move, each player has 30 legal moves instead of 20, since every major piece may be a knight (see the :doc:`tutorial`).

**Proposition 2 (legal moves are a union).**
For every legal history :math:`H`, a move is legal after :math:`H` if and only if it is legal in scramble chess under some arrangement :math:`A \in \mathrm{Cons}(H)`.

*Proof.* Under a fixed arrangement, :math:`H \cdot m` is a legal scramble chess game if and only if :math:`H` is, and :math:`m` is legal after :math:`H`.
Hence :math:`\mathrm{Cons}(H \cdot m) = \{A \in \mathrm{Cons}(H) : m \text{ is legal under } A\}`, which is nonempty if and only if such an :math:`A` exists. :math:`\square`

**Corollary 3 (end of the game).**
The player to move has no legal move if and only if, for every arrangement in :math:`\mathrm{Cons}(H)`, the corresponding game of scramble chess is over.
This is the end condition of the `original rules <http://antumbrastation.com/schroedinger-chess/2017/11/28/introduction-to-haft-schroedinger-chess.html>`_
(which do not mention draws by repetition or by the 50-move rule).

**Proposition 4 (lock-in is permanent).**
:math:`\mathrm{Cons}(H \cdot m) \subseteq \mathrm{Cons}(H)`.
In particular, once a nature becomes impossible for a piece, it stays impossible for the rest of the game.

*Proof.* This is the identity in the proof of Proposition 2. :math:`\square`

**Proposition 5 (kings are never captured).**
In a legal history, no piece that is captured can be a king, under any arrangement of :math:`\mathrm{Cons}(H)`.
Consequently, a game never ends with the capture of a king, and a player whose major pieces have all been captured but one knows that this one is their king.

*Proof.* Suppose the piece on square :math:`s` is captured by move :math:`m_t`.
Under an arrangement :math:`A` where it is the king, the capturing piece already attacked :math:`s` after move :math:`m_{t-1}`.
So the player who played :math:`m_{t-1}` left their king in check, and :math:`A \notin \mathrm{Cons}(H)`.
(If :math:`t = 1`, no capture is possible.) :math:`\square`

Termination
-----------

**Proposition 6 (games can last forever).**
Without a rule limiting the number of moves, there are infinite legal games.

*Proof.* Consider the moves Nb1-c3, Ng8-f6, Nc3-b1, Nf6-g8 repeated forever.
Under the standard arrangement, this is a legal game of chess, so the whole sequence is legal by Proposition 1. :math:`\square`

>>> from schroedingerchess.chess import ChessBoard
>>> cb = ChessBoard()
>>> for _ in range(10):
...     for move in ["b1c3", "g8f6", "c3b1", "f6g8"]:
...         _ = cb.move(*cb.translate_move((move[:2], move[2:])), disp=False)
>>> cb.time
40

Threefold repetition is ill-suited to this variant, since a position does not describe the state of the game: the history matters.
The 50-move rule, which only depends on the history, does guarantee termination, and this implementation applies it:
after 50 moves by each player without any capture or pawn move, the game is drawn, unless the last move was a checkmate.
It can be disabled with ``ChessBoard(fifty_move_rule=False)``.

>>> for _ in range(15):
...     for move in ["b1c3", "g8f6", "c3b1", "f6g8"]:
...         _ = cb.move(*cb.translate_move((move[:2], move[2:])), disp=False)
>>> cb.halfmove_clock
100
>>> cb.end_game()
'Draw by the 50-move rule'


**Proposition 7 (termination with the 50-move rule).**
If a game ends after 100 consecutive half-moves without a capture or a pawn move, as it does here, then every game lasts at most :math:`127 \times 100 + 126 = 12826` half-moves.

*Proof.* Each of the 16 pawns makes at most 6 moves before promoting or being blocked forever, which gives at most 96 pawn moves.
By Proposition 5 the kings are never captured, so there are at most 30 captures.
Hence there are at most 126 "irreversible" half-moves, and at most 100 half-moves between two of them, before the first one and after the last one. :math:`\square`

Who wins?
---------

When the player to move has no legal move, each arrangement of :math:`\mathrm{Cons}(H)` describes a game of scramble chess
that ends either by checkmate (the player to move is in check) or by stalemate.
The opponent cannot be in check, since they just played a legal move under every arrangement.
So there are three possibilities, which :meth:`~schroedingerchess.chess.ChessBoard.end_game` distinguishes:

- every arrangement gives a checkmate: the player to move lost;
- every arrangement gives a stalemate: the game is drawn;
- some arrangements give a checkmate and others a stalemate: the result is undetermined.

In particular, the player to move can never win, and the uncertainty is always between a loss and a draw.

**Theorem 8 (the result can be undetermined).**
There is a legal game of Haft Schrödinger chess that ends (the player to move has no legal move)
with a checkmate under some compatible arrangements and a stalemate under others.

*Proof.* The following game was found with a computer search, and is checked here with both solvers.
In the first 33 half-moves, white captures every black piece except the one on a8, which is therefore the black king (Proposition 5),
while the white pieces from c1 and f1 never move.
Then white pushes pawns to a6, b6 and c7 while the black king walks between a8 and b8,
and the piece from c1 travels to g7 along diagonals only, so that it can be the queen or a bishop.

>>> prefix = (
...     "g1f3 g7g5 f3g5 d8e6 g5e6 c7c5 e6f8 g8g6 f8d7 b8g3 f2g3 f7f6 d7c5 a7a6 "
...     "c5b7 c8d8 b7d8 e7e6 d8e6 g6g7 e6g7 h7h5 g7h5 h8g7 h5g7 e8h5 g7h5 a6a5 "
...     "h5f6 a5a4 f6g8 a4a3 b1a3 a8b8 a3b1 b8a8 a2a4 a8b8 a4a5 b8a8 a5a6 a8b8 "
...     "b2b4 b8a8 b4b5 a8b8 b5b6 b8a8 c2c4 a8b8 c4c5 b8a8 c1b2 a8b8"
... ).split()
>>> def play(moves, solver):
...     cb = ChessBoard(solver=solver)
...     for move in moves:
...         cb.move(*cb.translate_move((move[:2], move[2:])), disp=False)
...     return cb
>>> ending = "b2g7 b8a8 c5c6 a8b8 c6c7 b8a8 g7f8".split()
>>> cb = play(prefix + ending, solver="enumeration")
>>> cb.all_legal_moves()
[]
>>> cb.all_legal_natures(cb.grid[5][7])  # the piece from c1, now on f8
['Q', 'B']
>>> cb.end_game()
'Result unclear'
>>> play(prefix + ending, solver="ilp").end_game()
'Result unclear'

In the final position, the black king on a8 cannot move: a7, b7 and b8 are attacked by the white pawns, under every arrangement.
If the piece on f8 is the queen, it attacks a8 along the eighth rank, and black is checkmated.
If it is a bishop, nothing attacks a8, and black is stalemated.
Both arrangements are compatible with the whole history. :math:`\square`

Changing the last moves gives a definite stalemate (the piece from c1 stays on g7), or a definite checkmate (it goes to d4, from where it covers a7 whatever its nature, and a pawn gives check):

>>> play(prefix + "b2g7 b8a8 c5c6 a8b8 c6c7 b8a8 h2h3".split(), "enumeration").end_game()
'Stalemate'
>>> play(prefix + "b2d4 b8a8 c5c6 a8b8 c6c7 b8a8 b6b7".split(), "enumeration").end_game()
'Current player checkmated'

The original rules do not say what happens in the undetermined case.
A natural convention, in the spirit of the game, is to only declare a checkmate when every compatible arrangement gives one, and a draw otherwise.

Complexity
----------

**Proposition 9 (legality is easy).**
Deciding whether a history of length :math:`T` is legal takes time :math:`O(T)`.

*Proof.* Each player has at most 8 promoted pieces, so at most :math:`5040 \times 4^8` arrangements.
The enumeration of :mod:`schroedingerchess.enumeration` checks each arrangement against each of the 8 possible enemy kings at each time step,
and then combines both players in constant time, which takes :math:`O(T)` operations with a (very large) constant. :math:`\square`

In practice, the constant is small when few pawns have been promoted (see :doc:`benchmark`).
So, unlike some combinatorial problems that integer programming is used for, legality in this game is not computationally hard:
the integer program is a convenient formulation rather than a necessity.

Open questions
--------------

- What is the shortest game ending with an undetermined result? The example above has 61 half-moves and was not optimized.
- Can the result be undetermined in a position where both players still have major pieces whose natures are unknown?
- Is there a natural game-theoretic definition of the value of a position where the outcome depends on the arrangement, for instance as a game of imperfect information where an adversary or nature chooses the arrangement at the end?
