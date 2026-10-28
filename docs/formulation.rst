Mathematical formulation
========================

Intuition
---------

The game history (which piece went where, and when) is known to both players.
What is unknown is the nature of each back-rank piece.
A history is legal if we can assign a nature to every piece such that:

1. each player has the right number of pieces of each nature,
2. every move was possible for the nature of the piece that made it,
3. no player ever left their own king in check.

Constraints 1 and 2 only involve one piece at a time, or one player at a time.
Constraint 3 is the interesting one: it couples the natures of both players across the whole history.
For instance, "if my piece on a6 is my king, then your piece on a5 cannot be a rook".

All three constraints are linear in binary variables, so legality is the feasibility of an integer linear program (ILP).
It is implemented in :meth:`~schroedingerchess.chess.ChessBoard.quantum_explanation` with `PuLP <https://github.com/coin-or/pulp>`_,
and solved with `HiGHS <https://highs.dev/>`_.
By default, the game now solves the same problem by enumeration, which is faster (see :doc:`benchmark`).

Notations
---------

Sets
~~~~

- :math:`c \in \mathcal{C} = \{0, 1\}`: color (0 for white, 1 for black), and :math:`\bar{c} = 1 - c` the opposite color.
- :math:`i \in \mathcal{I} = \mathcal{M} \cup \mathcal{P} \cup \mathcal{R}`: index of a piece within its color, where

  - :math:`\mathcal{M} = \{0, \dots, 7\}` are the major (back-rank) pieces, numbered by their starting file,
  - :math:`\mathcal{P} = \{8, \dots, 15\}` are the pawns,
  - :math:`\mathcal{R} = \{16, \dots, 23\}` are the pieces created by promotion: pawn :math:`i` becomes piece :math:`i + 8`.

  The pieces with an unknown nature are :math:`\mathcal{U} = \mathcal{M} \cup \mathcal{R}`.
- :math:`n \in \mathcal{N} = \{K, Q, R, B, N\}`: nature of a piece with maximum quantities
  :math:`q_Q = 1`, :math:`q_R = q_B = q_N = 2`.
- :math:`s \in \mathcal{S}`: one of the 64 squares of the board.
- :math:`t \in \{0, \dots, T\}`: time, where :math:`T` is the number of moves played so far.
  At time :math:`t`, :math:`t` moves have been played and the player to move is :math:`c_t = t \bmod 2`.

Data
~~~~

These quantities are computed from the history, without knowing the natures:

- :math:`p_t(s, c, i) \in \{0, 1\}`: whether piece :math:`(c, i)` stands on square :math:`s` at time :math:`t`.
- :math:`a_t(s, c, i, n) \in \{0, 1\}`: whether piece :math:`(c, i) \in \mathcal{U}` attacks square :math:`s` at time :math:`t`, assuming it has nature :math:`n`.
  This depends on the geometry of the move and on the pieces in the way.
- :math:`a_t(s, c, i) \in \{0, 1\}`: whether pawn :math:`(c, i) \in \mathcal{P}` attacks square :math:`s` at time :math:`t`.
- :math:`F(c, i) \subseteq \mathcal{N}`: the natures for which one of the moves of piece :math:`(c, i)` was impossible.

Decision variables
~~~~~~~~~~~~~~~~~~

- :math:`z(c, i, n) \in \{0, 1\}` for :math:`(c, i, n) \in \mathcal{C} \times \mathcal{U} \times \mathcal{N}`:
  whether piece :math:`(c, i)` has nature :math:`n`.

From them, we deduce two linear expressions:

- the number of pieces of color :math:`c` attacking square :math:`s` at time :math:`t`

  .. math::

     d_t(c, s) = \sum_{i \in \mathcal{U}} \sum_{n \in \mathcal{N}} a_t(s, c, i, n) \, z(c, i, n) + \sum_{i \in \mathcal{P}} a_t(s, c, i)

- whether the king of color :math:`c` stands on square :math:`s` at time :math:`t`

  .. math::

     k_t(c, s) = \sum_{i \in \mathcal{M}} p_t(s, c, i) \, z(c, i, K)

Constraints
-----------

The problem has no objective: we only look for a feasible :math:`z`.

Each piece has exactly one nature:

.. math::

   \forall c \in \mathcal{C}, \forall i \in \mathcal{U}, \quad \sum_{n \in \mathcal{N}} z(c, i, n) = 1

Each player has exactly one king among the major pieces, and promoted pieces cannot be kings:

.. math::

   \forall c \in \mathcal{C}, \quad \sum_{i \in \mathcal{M}} z(c, i, K) = 1
   \qquad \text{and} \qquad
   \forall i \in \mathcal{R}, \quad z(c, i, K) = 0

The other natures have a limited quantity among the major pieces:

.. math::

   \forall c \in \mathcal{C}, \forall n \in \{Q, R, B, N\}, \quad \sum_{i \in \mathcal{M}} z(c, i, n) \leq q_n

Every move was possible for the nature of the piece:

.. math::

   \forall c \in \mathcal{C}, \forall i \in \mathcal{U}, \forall n \in F(c, i), \quad z(c, i, n) = 0

After each move, the player who just moved is not in check:

.. math::

   \forall t \in \{1, \dots, T\}, \forall s \in \mathcal{S}, \quad
   d_t(c_t, s) \leq 16 \, \big(1 - k_t(\bar{c}_t, s)\big)

The last constraint is a big-M formulation: if the king of :math:`\bar{c}_t` stands on :math:`s`, then :math:`k_t(\bar{c}_t, s) = 1` and nobody may attack :math:`s`.
Otherwise the right-hand side is 16, which is at least the number of pieces of color :math:`c_t` on the board, so the constraint is inactive.

Remarks
-------

**The arrangement is a permutation.**
Since there are 8 major pieces and :math:`1 + q_Q + q_R + q_B + q_N = 8`, all the quantity constraints are tight in any feasible solution.
Thus, the natures of the major pieces of each player form a permutation of RNBQKBNR.
There are :math:`\frac{8!}{2! \, 2! \, 2!} = 5040` such permutations per player, compared with 960 in Fischer random chess
(which requires bishops on opposite colors and the king between the rooks).

**Captured pieces are not kings.**
No constraint explicitly says so, but it follows from the check constraint.
If a piece on square :math:`s` is captured at time :math:`t`, the capturing piece attacked :math:`s` at time :math:`t-1`
(with its actual nature, otherwise the move would be forbidden).
So :math:`d_{t-1}(c_{t-1}, s) \geq 1`, which forces :math:`k_{t-1}(\bar{c}_{t-1}, s) = 0`.

**Questions answered with the same model.**

- Is a move legal? Append it to the history and check feasibility (:meth:`~schroedingerchess.chess.ChessBoard.test_move`).
- Can piece :math:`(c, i)` have nature :math:`n`? Add :math:`z(c, i, n) = 1` and check feasibility (:meth:`~schroedingerchess.chess.ChessBoard.is_legal_nature`).
- Is the current player possibly checkmated? When they have no legal move, add the constraint
  :math:`k_T(c_T, s) \leq d_T(\bar{c}_T, s)` for all :math:`s` (their king is attacked) or its negation (it is not),
  and check feasibility of both (:meth:`~schroedingerchess.chess.ChessBoard.end_game`).

**Speeding things up.**
Before solving the ILP, :meth:`~schroedingerchess.chess.ChessBoard.trivial_test_move` rejects moves that are impossible for every nature,
and the attack data is only computed for natures that are still possible.
These are shortcuts: they do not change the set of legal moves.
