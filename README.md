# Schrödinger Chess

[![Test](https://github.com/gdalle-bot/SchroedingerChess/actions/workflows/test.yml/badge.svg)](https://github.com/gdalle-bot/SchroedingerChess/actions/workflows/test.yml)
[![Docs](https://github.com/gdalle-bot/SchroedingerChess/actions/workflows/docs.yml/badge.svg)](https://gdalle-bot.github.io/SchroedingerChess/)

An implementation of [Haft Schrödinger chess](http://antumbrastation.com/schroedinger-chess/2017/11/28/introduction-to-haft-schroedinger-chess.html), a chess variant where pieces decide what they want to be.

## Rules in a nutshell

At the start, the eight back-rank pieces of each player have no fixed type.
They acquire one through the moves they make: a piece that jumps like a knight is a knight, a piece that moves along a long diagonal is a bishop or the queen, and so on.
A move is legal as long as there is at least one way to assign types to the pieces (one king, one queen, two rooks, two bishops and two knights per player) under which every move played so far was a legal chess move.
In particular, no player may ever have left their king in check, wherever their king actually is.

Checking this condition is a combinatorial problem, solved here with integer linear programming ([PuLP](https://github.com/coin-or/pulp) and [HiGHS](https://highs.dev/)).

## Getting started

Install [uv](https://docs.astral.sh/uv/), clone this repository, and launch the graphical interface from its root:

```bash
uv run schroedingerchess
```

You can play a local game with two players on the same screen, or an online game.
To host online games, start a server with `uv run schroedingerchess-server`.

Alternatively, `pip install .` installs the package (Python 3.12 or later) and the same two commands.

## Documentation

The [documentation](https://gdalle-bot.github.io/SchroedingerChess/) contains the rules and the API reference.

## Development

```bash
uv run pytest                                      # tests
uv run ruff check && uv run ruff format            # lint and format
uv run --group docs sphinx-build docs docs/_build  # documentation
```

Continuous integration runs all of these on every pull request.

## Credits

This project was started in 2018 by Guillaume Dalle, Maxime Godin and Lao-tseu.
The rules of the game come from [Antumbra Station](http://antumbrastation.com/).
