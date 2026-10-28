"""Game engines, which connect the display to a local or remote chess board."""

from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol
from twisted.internet.task import LoopingCall
from twisted.python import log

from .chess import ChessBoard, IllegalMove, LightBoard, square_name
from .client import ChessClientProtocol
from .display import ChessDisplay

FRAME_PER_SECOND = 30
CONNECTION_WAITING_TIME = 10  # seconds


class GameEngine:
    # TODO fix JSON encore / decode error
    """Base game engine, used while in the menu."""

    def start(self):
        """Starts the game engine. Create the window and initiate the reaction loop."""
        self.lightBoard = LightBoard()
        self.display = ChessDisplay(self)
        self.loopingCall = LoopingCall(self.display.update)
        self.loopingCall.start(1 / FRAME_PER_SECOND).addErrback(log.err)
        reactor.run()

    def startFromEngine(self, engine):
        """Starts the game engine. Create the window and initiate the reaction loop."""
        self.lightBoard = LightBoard()
        self.display = engine.display
        self.loopingCall = engine.loopingCall
        self.resume()

    def stop(self):
        """Stops the game engine."""
        # self.loopingCall.stop() # causing an unhandled error and don't seem necessary
        # self.display = None
        reactor.stop()

    def suspend(self):
        """Suspends the reaction loop of the window."""
        self.loopingCall.stop()

    def resume(self):
        """Resumes the reaction loop of the window."""
        self.loopingCall.start(1 / FRAME_PER_SECOND).addErrback(log.err)

    def setTwoPlayersOnOneBoardMode(self):
        """Sets the engine on the two-players-on-one-board mode."""
        self.suspend()
        self.display.gameEngine = TwoPlayersOnOneBoard(self)
        self.display.gameEngine.resume()

    def setOnePlayerOnNetworkMode(self, name, address, color):
        """Sets the engine on the one-player-on-network mode."""
        self.suspend()
        self.display.gameEngine = OnePlayerOnNetwork(self, name, address, color)
        self.display.gameEngine.resume()

    def moveTask(self, x1, y1, x2, y2):
        """Task to perform when the display detects a move."""
        raise NotImplementedError

    def move(self, x1, y1, x2, y2):
        """Schedules a move task."""
        reactor.callLater(0, self.moveTask, x1, y1, x2, y2)

    def checkEndTask(self):
        """Task to perform to check whether the game has ended."""
        raise NotImplementedError

    def checkEnd(self):
        """Schedules an end check"""
        reactor.callLater(0, self.checkEndTask)

    def handleIllegalMove(self, reason):
        """Handles an illegal move."""
        self.display.handleIllegalMove(reason)

    def makeDisplayDrawBoard(self):
        """Makes the display redraw the board."""
        self.display.drawBoard(self.lightBoard)

    def makeDisplayDrawChecks(self, check_positions):
        """Make the display highlight the kings in check."""
        self.display.drawChecks(check_positions)

    def makeDisplayDrawChecksMates(self, checkmate_positions):
        """Make the display highlight the checkmated kings."""
        self.display.drawCheckMates(checkmate_positions)


class TwoPlayersOnOneBoard(GameEngine):
    """Game engine for two players sharing the same screen."""

    def __init__(self, gameEngine):
        """
        Constructor.

        :param gameEngine: The initial game engine.
        """
        self.chessBoard = ChessBoard()
        self.lightBoard = LightBoard()
        self.display = gameEngine.display
        self.loopingCall = gameEngine.loopingCall
        self.validMovesCounter = 0

    def updateLightBoard(self):
        """Recompute the possible natures of all pieces and redraw the board."""
        natures = self.chessBoard.all_possible_natures()
        for col in [0, 1]:
            for i, piece in enumerate(self.chessBoard.pieces[col]):
                if piece.position:
                    self.lightBoard.setPiece(
                        i + col * 24, piece.color, piece.position, natures[(col, i)]
                    )
                elif piece.position is False:
                    self.lightBoard.setPiece(
                        i + col * 24,
                        piece.color,
                        False,
                        self.lightBoard.pieces[i + col * 24]["natures"],
                    )
        self.makeDisplayDrawBoard()

    def moveTask(self, mov):
        """Play a move on the board and update the display."""
        x1, y1, x2, y2 = mov[0], mov[1], mov[2], mov[3]
        try:
            self.chessBoard.move(x1, y1, x2, y2, disp=False)
            self.lightBoard.move(x1, y1, x2, y2)
            # Update everything before the message triggers a redraw
            self.display.setLastMove(x1, y1, x2, y2)
            self.display.lightBoard = self.lightBoard
            color = "White" if (self.validMovesCounter % 2 == 0) else "Black"
            self.display.addMessage(
                f"{color}: {square_name(x1, y1)}-{square_name(x2, y2)}"
            )
            self.validMovesCounter += 1
            if self.chessBoard.is_fifty_move_draw():
                self.display.addMessage("Draw by the 50-move rule")
            self.updateLightBoard()
        except IllegalMove as e:
            self.handleIllegalMove(str(e))

    def move(self, x1, y1, x2, y2):
        """Schedule a move task."""
        d = Deferred()
        d.addCallback(self.moveTask).addErrback(log.err)  # DEBUG
        reactor.callLater(0, d.callback, (x1, y1, x2, y2))

    def autoMove(self):
        """Let the computer choose a move."""
        try:
            return self.chessBoard.auto_move()
        except IllegalMove as e:  # In case the game has ended
            self.handleIllegalMove(str(e))

    def checkEndTask(self):
        """Display the outcome of the game."""
        outcome = self.chessBoard.end_game()
        self.display.addMessage(outcome)


class OnePlayerOnNetwork(GameEngine):
    """Game engine for one player connected to a remote server."""

    def __init__(self, gameEngine, name, address=None, color=0):
        # raise NotImplementedError("Server not yet implemented")
        if not address:
            host, port = "localhost", 6000
        else:
            host, port = address.split(":")

        self.name = name
        self.color = color
        self.turn = -1  # 0 = White is playing, 1 = Black is playing
        self.lightBoard = gameEngine.lightBoard
        self.display = gameEngine.display
        if self.color == 1:  # 1 = black
            self.display.flipDisplay(True)

        self.loopingCall = gameEngine.loopingCall
        self.protocol = ChessClientProtocol(self)

        point = TCP4ClientEndpoint(reactor, host, int(port))  # connection point
        try:
            attempt = connectProtocol(point, self.protocol)
            attempt.addErrback(self.connectionFailed)
            attempt.addTimeout(
                CONNECTION_WAITING_TIME, reactor, onTimeoutCancel=self.connectionFailed
            )
            self.display.addMessage("Connecting to remote server...")
        except Exception:
            self.connectionFailed()

    def handleInit(self):
        """Handle the connection to the server."""
        self.display.addMessage("Connection established.")
        self.display.addMessage("Waiting for an opponent...")

    def handleReady(self):
        """Handle the start of the game."""
        self.display.addMessage("Found an opponent. White begins...")
        self.turn = 0

    def moveTask(self, x1, y1, x2, y2):
        """Send a move to the server."""
        if self.turn != self.color:
            self.handleIllegalMove(
                "It is not your turn: wait for your opponent to move"
            )
        else:
            msg = {"type": "move", "color": self.color, "description": (x1, y1, x2, y2)}
            self.protocol.sendMessage(msg)

    def autoMove(self):
        """Schedule an automatic move request."""
        reactor.callLater(0, self.autoMoveTask)

    def autoMoveTask(self):
        """Ask the server to choose a move."""
        if self.turn != self.color:
            self.handleIllegalMove(
                "It is not your turn: wait for your opponent to move"
            )
        else:
            msg = {"type": "automove", "color": self.color}
            self.protocol.sendMessage(msg)

    def checkEndTask(self):
        """Ask the server for the outcome of the game."""
        if self.turn == -1:
            self.addMessage("The game has not started yet")
        else:
            msg = {"type": "endgame", "color": self.color}
            self.protocol.sendMessage(msg)

    def handleMove(self, description):
        """Executes a move received from the server"""
        color = "White" if (self.turn == 0) else "Black"  # player who moved
        self.turn = (self.turn + 1) % 2
        x1, y1, x2, y2 = description
        self.lightBoard.move(x1, y1, x2, y2)
        self.display.setLastMove(x1, y1, x2, y2)
        self.display.lightBoard = self.lightBoard
        self.display.addMessage(f"{color}: {square_name(x1, y1)}-{square_name(x2, y2)}")
        # print("cb.move({},{},{},{})".format(x1, y1, x2, y2))

    def handleUpdateBoard(self, description):
        """Replace the board with the one sent by the server."""
        self.lightBoard.unwrap(description)
        self.makeDisplayDrawBoard()

    def handleChecks(self, description):
        """Highlight the kings in check."""
        self.makeDisplayDrawChecks(description)

    def handleCheckMates(self, description):
        """Highlight the checkmated kings."""
        self.makeDisplayDrawCheckMates(description)

    def connectionFailed(self, *kwargs):
        """Go back to the menu when the server cannot be reached."""
        self.display.setMenuMode()
        self.display.addMessage("The server could not be reached.")

    def handleDisconnection(self, description):
        # if self.display is None:
        # return
        """Go back to the menu after a disconnection."""
        self.display.addMessage("Disconnected from server")
        self.display.addMessage(description.__str__())
        self.suspend()
        self.display.gameEngine = GameEngine()
        self.display.gameEngine.startFromEngine(self)
        self.display.setMenuMode()
        # raise NotImplementedError
        # TODO implement disconnection screen
        # reactor.stop()
