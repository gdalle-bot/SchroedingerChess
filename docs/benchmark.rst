Integer program or enumeration?
===============================

The :doc:`formulation` decides whether a history is consistent with an integer linear program (ILP).
Since every player's arrangement is one of only 2880 permutations of RNBQKBNR,
we can also enumerate them. This page compares both approaches.

Enumeration
-----------

A naive enumeration would test all :math:`2880^2 \approx 8.3` million pairs of arrangements at every check.
:mod:`schroedingerchess.enumeration` exploits the structure of the problem instead:

1. For each player separately, keep the arrangements compatible with the moves of their own pieces.
   This only involves the sets :math:`F(c, i)` of forbidden natures.
2. The check constraints of an attacker :math:`c` only depend on the arrangement of :math:`c` and on *which piece* is the king of :math:`\bar{c}`.
   For every arrangement of :math:`c` and every candidate king :math:`k \in \mathcal{M}` of :math:`\bar{c}`, we test all time steps at once with numpy.
3. The history is consistent if and only if there are kings :math:`(k_0, k_1)` such that some arrangement of white with king :math:`k_0` allows the black king :math:`k_1`,
   and some arrangement of black with king :math:`k_1` allows the white king :math:`k_0`.
   This is an 8 × 8 table lookup.

The cost is :math:`O(2880 \times 8 \times T)` for a history of length :math:`T`, instead of :math:`O(2880^2 \times T)`.
Promoted pieces multiply the number of configurations of their color by 4 (queen, rook, bishop or knight).
Beyond :data:`~schroedingerchess.enumeration.MAX_CONFIGURATIONS` configurations, which requires many promotions,
the enumeration gives up and :meth:`~schroedingerchess.chess.ChessBoard.explanation` falls back on the ILP.

Both methods return the same answers: the tests compare them on random games,
including moves, possible natures and check conditions.
Comparing them also revealed a bug in the ILP's checkmate test, which ignored the squares that no piece could attack.

Results
-------

The script ``benchmarks/solvers.py`` plays 5 random games, and measures the median time of three tasks after a given number of moves:
one consistency check, listing all legal moves, and computing the possible natures of every piece in play (what the graphical interface does after each move).

These are the results on a 4-core Linux machine with Python 3.14, HiGHS 1.15 and numpy 2.5:

==============  ========  ========  ================  =======
Moves played    Task      ILP (ms)  Enumeration (ms)  Speedup
==============  ========  ========  ================  =======
0               check          6.6               0.6    11.7×
0               moves        360.7             165.2     2.2×
0               natures      566.7              39.3    14.4×
10              check         10.0               1.1     9.0×
10              moves        644.5             231.7     2.8×
10              natures      630.0              70.5     8.9×
20              check         14.7               1.7     8.8×
20              moves        836.9             261.0     3.2×
20              natures      570.0              65.0     8.8×
40              check         15.6               2.9     5.3×
40              moves        922.4             221.7     4.2×
40              natures      386.1              42.6     9.1×
60              check         21.8               4.3     5.1×
60              moves        882.8             206.4     4.3×
60              natures      375.8              35.2    10.7×
==============  ========  ========  ================  =======

Conclusion
----------

The enumeration is 5 to 12 times faster for a single check, so it is now the default solver
(``ChessBoard(solver="enumeration")``). The ILP is still available with ``ChessBoard(solver="ilp")``.

Listing the legal moves benefits less (2 to 4 times), because most of the remaining time is spent outside the solver:
for every candidate move, :meth:`~schroedingerchess.chess.ChessBoard.add_move_to_history` recomputes the attack tables in pure Python.
Vectorizing these computations, or caching the per-time-step results of the enumeration (the history only grows), would be the next steps.
