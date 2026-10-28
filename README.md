# SchroedingerChess

[![Join the chat at https://gitter.im/SchroedingerChess/Lobby](https://badges.gitter.im/SchroedingerChess/Lobby.svg)](https://gitter.im/SchroedingerChess/Lobby?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge) [![Build Status](https://travis-ci.org/gdalle/SchroedingerChess.svg?branch=master)](https://travis-ci.org/gdalle/SchroedingerChess)

Implementation of Haft Schroedinger Chess, where chess pieces decide what they want to be...

See the docs at https://gdalle.github.io/SchroedingerChess/

To run the code, you need Python 3.14 and a few dependencies:
```
python -m venv .venv
source .venv/bin/activate
pip install numpy pulp highspy twisted pygame-ce
```

Then, all it takes to play a game is to execute `python -m schroedingerchess` from the root of the repository.
To host an online game, start the server with `python -m schroedingerchess.server`.
