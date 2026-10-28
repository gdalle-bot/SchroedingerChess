Tutorial
========

This tutorial shows how to play Haft Schrödinger chess from Python, without the graphical interface.
All the examples are run as tests, so their output is up to date.

Creating a board
----------------

The main object is :class:`~schroedingerchess.chess.ChessBoard`.
Squares are designated by their coordinates ``(x, y)``, where ``x`` is the file (0 for a, 7 for h) and ``y`` the rank (0 for rank 1, 7 for rank 8).
The pieces are stored in ``grid[x][y]``.

>>> from schroedingerchess.chess import ChessBoard, IllegalMove
>>> cb = ChessBoard()
>>> piece = cb.grid[1][0]  # the piece on b1
>>> piece.color, piece.number
(0, 1)

At the start, the major pieces can have any nature, and the pawns are pawns:

>>> cb.all_legal_natures(cb.grid[1][0])
['K', 'Q', 'R', 'B', 'N']
>>> cb.all_legal_natures(cb.grid[1][1])
['P']

Since every major piece could be a knight, there are 30 legal first moves instead of 20:

>>> len(cb.all_legal_moves())
30

Playing moves
-------------

A move is given by its start and end coordinates.
:meth:`~schroedingerchess.chess.ChessBoard.translate_move` converts them to and from algebraic notation:

>>> cb.translate_move(("b1", "c3"))
(1, 0, 2, 2)

Let us jump with the piece on b1. After this move, it can only be a knight:

>>> cb.move(1, 0, 2, 2, disp=False)
True
>>> cb.all_legal_natures(cb.grid[2][2])
['N']

Illegal moves raise an :class:`~schroedingerchess.chess.IllegalMove` exception explaining why, and leave the board unchanged:

>>> cb.move(2, 2, 2, 4, disp=False)
Traceback (most recent call last):
...
schroedingerchess.chess.IllegalMove: It is Black's turn, but the piece on c3 is White: you cannot move out of turn

Entanglement between pieces
---------------------------

Each player has only two knights.
Once two pieces have jumped like knights, a third one cannot:

>>> cb.move(0, 6, 0, 5, disp=False)  # black plays a6
True
>>> cb.move(6, 0, 5, 2, disp=False)  # g1 jumps to f3
True
>>> cb.move(1, 6, 1, 5, disp=False)  # black plays b6
True

The piece on h1 cannot jump to g3 anymore:

>>> cb.move(7, 0, 6, 2, disp=False)
Traceback (most recent call last):
...
schroedingerchess.chess.IllegalMove: Moving from h1 to g3 is illegal for any initial piece configuration: it would contradict the previous moves, or leave the king in check

Entanglement between players
----------------------------

The king may never be left in check, wherever it is.
This creates constraints between the natures of both players.

>>> cb = ChessBoard()
>>> cb.move(4, 1, 4, 2, disp=False)  # white plays e3
True
>>> cb.move(3, 6, 3, 5, disp=False)  # black plays d6
True
>>> cb.move(5, 0, 1, 4, disp=False)  # the piece on f1 goes to b5
True

The piece on b5 moved along a diagonal, so it is a bishop or the queen (or the king, if it had moved by one square only):

>>> cb.all_legal_natures(cb.grid[1][4])
['Q', 'B']

It attacks the piece on e8 through the square d7, which black just vacated.
Black's king can still be on e8, as long as black parries the threat.
If black ignores it, the piece on e8 cannot be the king:

>>> "K" in cb.all_legal_natures(cb.grid[4][7])
True
>>> cb.move(0, 6, 0, 5, disp=False)  # black plays a6
True
>>> "K" in cb.all_legal_natures(cb.grid[4][7])
False

Saving a game
-------------

:mod:`schroedingerchess.export` writes games as text records in the PGN format, with moves in long algebraic notation, and reads them back:

>>> from schroedingerchess import export
>>> record = export.game_record(cb.moves)
>>> print(record.splitlines()[-1])
1. e2e3 d7d6 2. f1b5 a7a6 *
>>> export.read_game_record(record) == cb.moves
True

It can also render a game as an animated GIF, with :func:`~schroedingerchess.export.export_gif`.
In the graphical interface, the "Save as text" and "Save as GIF" buttons ask where to save the current game.

Playing against the computer
----------------------------

:meth:`~schroedingerchess.chess.ChessBoard.auto_move` chooses a legal move for the current player.
It guesses a nature for every piece, ranks the moves with a small alpha-beta search
(see :mod:`schroedingerchess.engine`), and returns the best one that is legal:

>>> move = cb.auto_move()
>>> cb.test_move(*move)
True

The guessed natures can be displayed in the terminal with ``cb.display_guess()``, and a complete game against the computer can be played in the terminal with ``cb.one_player_game()``.
