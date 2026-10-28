# SchroedingerChess

[![Join the chat at https://gitter.im/SchroedingerChess/Lobby](https://badges.gitter.im/SchroedingerChess/Lobby.svg)](https://gitter.im/SchroedingerChess/Lobby?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge) [![Test](https://github.com/gdalle-bot/SchroedingerChess/actions/workflows/test.yml/badge.svg)](https://github.com/gdalle-bot/SchroedingerChess/actions/workflows/test.yml)

Implementation of Haft Schroedinger Chess, where chess pieces decide what they want to be...

See the docs at https://gdalle.github.io/SchroedingerChess/

To run the code, install [uv](https://docs.astral.sh/uv/) and clone this repository. Then, all it takes to play a game is to execute
```
uv run schroedingerchess
```
from the root of the repository.
Alternatively, `pip install .` installs the package and its dependencies (Python 3.12 or later) into your current environment.

To host an online game, start the server with `uv run schroedingerchess-server`.

## Development

Run the tests with `uv run pytest`, and lint and format the code with `uv run ruff check` and `uv run ruff format`.
