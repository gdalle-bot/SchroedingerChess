"""Launch the graphical client with ``python -m schroedingerchess``."""

from .game_engines import GameEngine


def main():
    """Start the graphical game client."""
    GameEngine().start()


if __name__ == "__main__":
    main()
