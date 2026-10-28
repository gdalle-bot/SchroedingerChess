"""Graphical interface of the game, drawn with pygame."""

import os
import time

import pygame

from .chess import LightBoard

ASSETS_DIR = os.path.dirname(os.path.abspath(__file__))
UI_FONTS = "inter,segoeui,helveticaneue,arial,dejavusans"

# Geometry
SQUARE = 80
BOARD = 8 * SQUARE
PANE = 340
PADDING = 20
RADIUS = 10

# Colors
BACKGROUND = (32, 34, 39)
CARD = (45, 48, 55)
CARD_HOVER = (58, 62, 71)
CARD_PRESSED = (70, 75, 86)
BORDER = (70, 75, 86)
TEXT = (232, 234, 238)
MUTED = (150, 156, 168)
ACCENT = (96, 156, 230)
ACCENT_HOVER = (120, 174, 240)
LIGHT_SQUARE = (222, 227, 230)
DARK_SQUARE = (140, 162, 173)
LAST_MOVE = (246, 224, 94, 120)
SELECTION = (96, 156, 230, 130)
CHECK = (232, 70, 60, 150)
ERROR = (214, 64, 58)
ERROR_SQUARE = (232, 70, 60, 110)
ERROR_DURATION = 3.0  # seconds during which an error stays on screen


def _font(size, bold=False):
    return pygame.font.SysFont(UI_FONTS, size, bold=bold)


def _wrap(text, font, width):
    """Split a text into lines that fit in ``width`` pixels."""
    lines, line = [], ""
    for word in text.split(" "):
        candidate = word if not line else line + " " + word
        if font.size(candidate)[0] <= width or not line:
            line = candidate
        else:
            lines.append(line)
            line = word
    lines.append(line)
    return lines


class Button:
    """Clickable rounded button.

    :param rect: Position and size of the button.
    :param label: Text displayed on the button.
    :param primary: Whether the button is highlighted with the accent color.
    """

    def __init__(self, rect, label, primary=False):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.primary = primary

    def draw(self, screen, font, hovered=False, pressed=False):
        """Draw the button, depending on the mouse state."""
        if self.primary:
            color = ACCENT_HOVER if hovered or pressed else ACCENT
            text_color = (255, 255, 255)
        else:
            color = CARD_PRESSED if pressed else CARD_HOVER if hovered else CARD
            text_color = TEXT
        pygame.draw.rect(screen, color, self.rect, border_radius=RADIUS)
        if not self.primary:
            pygame.draw.rect(screen, BORDER, self.rect, 1, border_radius=RADIUS)
        text = font.render(self.label, True, text_color)
        screen.blit(text, text.get_rect(center=self.rect.center))


class InputBox:
    """Text input field.

    :param x: Horizontal position of the box, in pixels.
    :param y: Vertical position of the box, in pixels.
    :param w: Width of the box, in pixels.
    :param h: Height of the box, in pixels.
    :param text: Initial text.
    """

    def __init__(self, x, y, w, h, text=""):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.font = _font(18)
        self.active = False
        self.has_change = False

    def handle_event(self, event):
        """Update the box after a mouse or keyboard event."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
            self.has_change = True
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.unicode and event.unicode.isprintable():
                self.text += event.unicode
            self.has_change = True

    def update(self):
        """Kept for compatibility: the box has a fixed size."""

    def draw(self, screen):
        """Draw the box on the screen."""
        pygame.draw.rect(screen, BACKGROUND, self.rect, border_radius=RADIUS)
        border = ACCENT if self.active else BORDER
        pygame.draw.rect(screen, border, self.rect, 2, border_radius=RADIUS)
        text = self.font.render(self.text, True, TEXT)
        clip = screen.get_clip()
        screen.set_clip(self.rect.inflate(-16, 0))
        y = self.rect.centery - text.get_height() // 2
        x = self.rect.x + 10
        if self.active:
            # Keep the end of the text and the cursor visible
            x = min(x, self.rect.right - 14 - text.get_width())
        screen.blit(text, (x, y))
        if self.active:
            cursor_x = x + text.get_width() + 2
            pygame.draw.line(
                screen, TEXT, (cursor_x, y + 2), (cursor_x, y + text.get_height() - 2)
            )
        screen.set_clip(clip)


class ChessDisplay:
    """Window showing the board, the menus and a side pane.

    :param gameEngine: Game engine receiving the actions of the user.
    """

    def __init__(self, gameEngine):
        """Create the window."""
        os.environ["SDL_VIDEO_CENTERED"] = "1"
        self.width = BOARD
        self.height = BOARD
        self.pane_width = PANE
        self.total_width = BOARD + PANE
        self.total_height = BOARD

        pygame.init()
        self.screen = pygame.display.set_mode((self.total_width, self.total_height))
        pygame.display.set_caption("Schrödinger Chess")

        self.state = "MENU"  # MENU or PLAYING
        self.mode = "NONE"  # LOCAL or ONLINE once playing
        self.menuState = "START"  # START or ONLINE

        self.title_font = _font(32, bold=True)
        self.title_font_small = _font(24, bold=True)
        self.font = _font(18)
        self.font_bold = _font(18, bold=True)
        self.small_font = _font(15)
        self.coord_font = _font(13, bold=True)
        self.load_images()

        self.gameEngine = gameEngine
        self.lightBoard = None

        self.selectedBox = None  # Selected square, in screen coordinates
        self.last_move = (-1, -1, -1, -1)  # x1, y1, x2, y2 coordinates
        self.flip = False  # Whether the board is upside down (black at the bottom)
        self.check_positions = [[False] * 8 for _ in range(8)]
        self.checkmate_positions = [[False] * 8 for _ in range(8)]

        self.message_history = []
        self.current_first_message = 0
        self.pressed = None  # Name of the button being pressed
        self.error = None  # Last error, shown in a banner over the board
        self.error_time = 0.0
        self.error_lines = set()  # Indices of the error lines in the log
        self.attempted_move = None  # Move being checked, flashed if illegal

        card = self._menu_card()
        field_w = card.width - 2 * PADDING
        self.name = InputBox(card.x + PADDING, card.y + 200, field_w, 40, "player")
        self.address = InputBox(
            card.x + PADDING, card.y + 270, field_w, 40, "127.0.0.1:6000"
        )
        self.input_boxes = [self.name, self.address]
        self.selected_color = "W"

        self.addMessage("Please select a game mode")

    # Modes

    def setMenuMode(self):
        """Go back to the main menu."""
        if self.state == "PLAYING":
            self.state = "MENU"
            self.selectedBox = None
            self.render()

    def setTwoPlayersOnOneBoardMode(self):
        """Start a game with two players on the same screen."""
        if self.state == "MENU":
            self.state = "PLAYING"
            self.mode = "LOCAL"
            self.last_move = (-1, -1, -1, -1)
            self.flip = False
            self.gameEngine.setTwoPlayersOnOneBoardMode()
            self.gameEngine.makeDisplayDrawBoard()
            self.addMessage("Started local game")

    def setOnePlayerOnNetworkMode(self, name, address, color):
        """Start a game against a remote player."""
        if self.state == "MENU":
            self.state = "PLAYING"
            self.mode = "ONLINE"
            self.last_move = (-1, -1, -1, -1)
            self.flip = False
            self.gameEngine.setOnePlayerOnNetworkMode(name, address, color)
            self.gameEngine.makeDisplayDrawBoard()

    # Methods called by the game engines

    def drawBoard(self, lightBoard):
        """Draw the board.

        :param lightBoard: The :class:`~schroedingerchess.chess.LightBoard` to draw.
        """
        self.lightBoard = lightBoard
        self.render()

    def drawChecks(self, check_positions):
        """Highlight the kings in check.

        :param check_positions: List of the check positions.
        """
        self.check_positions = [[False] * 8 for _ in range(8)]
        for x, y in check_positions:
            self.check_positions[x][y] = True
        self.gameEngine.makeDisplayDrawBoard()

    def drawCheckMates(self, checkmate_positions):
        """Highlight the checkmated kings.

        :param checkmate_positions: List of the checkmate positions.
        """
        self.checkmate_positions = [[False] * 8 for _ in range(8)]
        for x, y in checkmate_positions:
            self.checkmate_positions[x][y] = True
        self.gameEngine.makeDisplayDrawBoard()

    def handleIllegalMove(self, reason):
        """Show prominently why a move is illegal.

        The reason appears in a red banner over the board for a few seconds,
        the squares of the attempted move are highlighted in red, and the
        reason is logged in red.

        :param reason: Reason of the illegal move.
        """
        self.showError(reason)

    def showError(self, message):
        """Show an error in a red banner over the board, and in the log."""
        self.error = message
        self.error_time = time.monotonic()
        self.addMessage(message, error=True)

    def setLastMove(self, x1, y1, x2, y2):
        """Remember the last move, to highlight it."""
        self.last_move = (x1, y1, x2, y2)
        self.error = None
        self.attempted_move = None

    def flipDisplay(self, newState):
        """Set the display orientation.

        :param newState: True if the display has to be upside down
            (Black in the lower part)
        """
        self.flip = newState
        self.gameEngine.makeDisplayDrawBoard()

    def flipY(self, y):
        """Convert a rank into a row of the screen, and conversely.

        :param y: The y coordinate.
        """
        return y if self.flip else 7 - y

    def addMessage(self, message, error=False):
        """Add a message to the log, and scroll to the end.

        :param message: A string message.
        :param error: Whether to show the message in red.
        """
        width = self._log_rect().width - 2 * 12
        lines = _wrap(message, self.small_font, width)
        if error:
            start = len(self.message_history)
            self.error_lines.update(range(start, start + len(lines)))
        self.message_history.extend(lines)
        self.current_first_message = max(
            0, len(self.message_history) - self._max_messages()
        )
        self.render()

    # Event loop

    def update(self):
        """Handle the pending events and redraw the window."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.gameEngine.stop()
                return
            if event.type == pygame.MOUSEWHEEL:
                if self._log_rect().collidepoint(pygame.mouse.get_pos()):
                    self.scrollMessages(-event.y)
            elif self.state == "MENU":
                self.updateMenu(event)
            elif self.state == "PLAYING":
                self.updateBoard(event)
                self.updatePane([event])
        self.render()

    def scrollMessages(self, lines):
        """Scroll the message log by a number of lines."""
        last = max(0, len(self.message_history) - self._max_messages())
        self.current_first_message = min(
            last, max(0, self.current_first_message + lines)
        )

    def _clicked(self, event, buttons):
        """Return the name of the button clicked by ``event``, if any."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.pressed = None
            for name, button in buttons.items():
                if button.rect.collidepoint(event.pos):
                    self.pressed = name
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            pressed, self.pressed = self.pressed, None
            if pressed in buttons and buttons[pressed].rect.collidepoint(event.pos):
                return pressed
        return None

    def updateMenu(self, event):
        """Handle an event in the menu."""
        if self.menuState == "ONLINE":
            for box in self.input_boxes:
                box.handle_event(event)
        clicked = self._clicked(event, self._menu_buttons())
        if clicked == "local":
            self.setTwoPlayersOnOneBoardMode()
        elif clicked == "online":
            self.menuState = "ONLINE"
        elif clicked == "quit":
            self.gameEngine.stop()
        elif clicked == "back":
            self.menuState = "START"
        elif clicked == "white":
            self.selected_color = "W"
        elif clicked == "black":
            self.selected_color = "B"
        elif clicked == "connect":
            if not self.check_address_format(self.address.text):
                self.showError('Please enter a valid address, like "127.0.0.1:6000"')
            elif len(self.name.text) == 0:
                self.showError("Please enter a player name")
            else:
                color = 0 if self.selected_color == "W" else 1
                self.setOnePlayerOnNetworkMode(self.name.text, self.address.text, color)

    def updateBoard(self, event):
        """Handle piece selection and move attempts."""
        if event.type != pygame.MOUSEBUTTONUP:
            return
        x, y = event.pos
        if event.button != 1 or x >= BOARD or y >= BOARD:
            self.selectedBox = None
            return
        box = (x // SQUARE, y // SQUARE)
        if self.selectedBox is None:
            self.selectedBox = box
        elif self.selectedBox == box:
            self.selectedBox = None
        else:
            x1, y1 = self.selectedBox[0], self.flipY(self.selectedBox[1])
            x2, y2 = box[0], self.flipY(box[1])
            self.selectedBox = None
            self.attempted_move = (x1, y1, x2, y2)
            self.gameEngine.move(x1, y1, x2, y2)

    def updatePane(self, events=()):
        """Handle the clicks on the side pane buttons, and redraw."""
        for event in events:
            clicked = self._clicked(event, self._pane_buttons())
            if clicked == "auto":
                if self.mode == "LOCAL":
                    move = self.gameEngine.autoMove()
                    if move is not None:
                        self.gameEngine.move(*move)
                else:
                    self.gameEngine.autoMove()
            elif clicked == "end":
                self.gameEngine.checkEnd()
            elif clicked == "flip":
                self.flipDisplay(not self.flip)
            elif clicked == "menu":
                self.setMenuMode()
        self.render()

    # Layout

    def _menu_card(self):
        return pygame.Rect((BOARD - 400) // 2, (BOARD - 440) // 2, 400, 440)

    def _log_rect(self):
        top = 300 if self.state == "PLAYING" else 90
        return pygame.Rect(BOARD + PADDING, top, PANE - 2 * PADDING, BOARD - top - 130)

    def _max_messages(self):
        return max(1, (self._log_rect().height - 16) // self.small_font.get_linesize())

    def _menu_buttons(self):
        card = self._menu_card()
        x, w = card.x + PADDING, card.width - 2 * PADDING
        if self.menuState == "START":
            return {
                "local": Button((x, card.y + 170, w, 56), "Local game", primary=True),
                "online": Button((x, card.y + 240, w, 56), "Online game"),
                "quit": Button((x, card.y + 340, w, 48), "Quit"),
            }
        half = (w - 10) // 2
        return {
            "white": Button((x, card.y + 110, half, 44), "White"),
            "black": Button((x + half + 10, card.y + 110, half, 44), "Black"),
            "connect": Button((x, card.y + 340, half, 48), "Connect", primary=True),
            "back": Button((x + half + 10, card.y + 340, half, 48), "Back"),
        }

    def _pane_buttons(self):
        if self.state != "PLAYING":
            return {}
        x, w = BOARD + PADDING, (PANE - 2 * PADDING - 10) // 2
        buttons = {
            "auto": Button((x, 170, w, 48), "Auto-move", primary=True),
            "end": Button((x + w + 10, 170, w, 48), "Game over?"),
            "flip": Button((x, 228, w, 48), "Flip board"),
        }
        if self.mode == "LOCAL":
            buttons["menu"] = Button((x + w + 10, 228, w, 48), "Main menu")
        return buttons

    # Drawing

    def render(self):
        """Redraw the whole window."""
        self.screen.fill(BACKGROUND)
        if self.state == "PLAYING" and self.lightBoard is not None:
            self._draw_board(self.lightBoard)
        else:
            self.drawMenu()
        self.drawPane()
        self._draw_error()
        pygame.display.flip()

    def _error_alpha(self):
        """Opacity of the error banner, which fades out at the end."""
        if self.error is None:
            return 0
        age = time.monotonic() - self.error_time
        if age > ERROR_DURATION:
            self.error = None
            self.attempted_move = None
            return 0
        return min(1.0, 2 * (ERROR_DURATION - age))

    def _draw_error(self):
        alpha = self._error_alpha()
        if alpha == 0:
            return
        if self.state == "PLAYING" and self.attempted_move is not None:
            x1, y1, x2, y2 = self.attempted_move
            r, g, b, a = ERROR_SQUARE
            for x, y in [(x1, y1), (x2, y2)]:
                self._overlay(self._square_rect(x, y), (r, g, b, int(a * alpha)))
        lines = _wrap(self.error, self.font_bold, BOARD - 6 * PADDING)
        height = 2 * PADDING + len(lines) * self.font_bold.get_linesize()
        banner = pygame.Rect(
            2 * PADDING, BOARD - 2 * PADDING - height, BOARD - 4 * PADDING, height
        )
        surface = pygame.Surface(banner.size, pygame.SRCALPHA)
        pygame.draw.rect(
            surface,
            (*ERROR, int(240 * alpha)),
            surface.get_rect(),
            border_radius=RADIUS,
        )
        for i, line in enumerate(lines):
            text = self.font_bold.render(line, True, (255, 255, 255))
            text.set_alpha(int(255 * alpha))
            y = PADDING + i * self.font_bold.get_linesize()
            surface.blit(text, text.get_rect(midtop=(banner.width // 2, y)))
        self.screen.blit(surface, banner.topleft)

    def _overlay(self, rect, color):
        surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        surface.fill(color)
        self.screen.blit(surface, rect.topleft)

    def _square_rect(self, x, y):
        """Rectangle of the square with board coordinates ``(x, y)``."""
        return pygame.Rect(x * SQUARE, self.flipY(y) * SQUARE, SQUARE, SQUARE)

    def _draw_board(self, lightBoard):
        for x in range(8):
            for y in range(8):
                light = (x + y) % 2 == 1
                rect = self._square_rect(x, y)
                color = LIGHT_SQUARE if light else DARK_SQUARE
                pygame.draw.rect(self.screen, color, rect)
                coord_color = DARK_SQUARE if light else LIGHT_SQUARE
                if self.flipY(y) == 7:
                    label = self.coord_font.render("abcdefgh"[x], True, coord_color)
                    corner = rect.move(-4, -2).bottomright
                    self.screen.blit(label, label.get_rect(bottomright=corner))
                if x == 0:
                    label = self.coord_font.render(str(y + 1), True, coord_color)
                    self.screen.blit(label, rect.move(4, 3).topleft)

        if self.state == "PLAYING":
            if self.last_move[0] >= 0:
                x1, y1, x2, y2 = self.last_move
                self._overlay(self._square_rect(x1, y1), LAST_MOVE)
                self._overlay(self._square_rect(x2, y2), LAST_MOVE)
            for x in range(8):
                for y in range(8):
                    if self.check_positions[x][y] or self.checkmate_positions[x][y]:
                        self._overlay(self._square_rect(x, y), CHECK)
            if self.selectedBox is not None:
                sx, sy = self.selectedBox
                self._overlay(self._square_rect(sx, self.flipY(sy)), SELECTION)

        for piece in lightBoard.pieces:
            if piece["position"]:
                rect = self._square_rect(*piece["position"])
                self.draw_piece(piece["color"], piece["natures"], *rect.topleft, SQUARE)

    def drawMenu(self):
        """Draw the main menu over a dimmed starting position."""
        flip, self.flip = self.flip, False
        self._draw_board(LightBoard())
        self.flip = flip
        self._overlay(pygame.Rect(0, 0, BOARD, BOARD), (20, 22, 26, 190))

        card = self._menu_card()
        pygame.draw.rect(self.screen, CARD, card, border_radius=2 * RADIUS)
        pygame.draw.rect(self.screen, BORDER, card, 1, border_radius=2 * RADIUS)
        mouse = pygame.mouse.get_pos()
        buttons = self._menu_buttons()

        if self.menuState == "START":
            title = self.title_font.render("Schrödinger Chess", True, TEXT)
            self.screen.blit(title, title.get_rect(midtop=(card.centerx, card.y + 40)))
            for i, line in enumerate(
                ["Chess where pieces decide", "what they want to be"]
            ):
                text = self.font.render(line, True, MUTED)
                center = (card.centerx, card.y + 100 + 24 * i)
                self.screen.blit(text, text.get_rect(midtop=center))
        else:
            title = self.title_font_small.render("Online game", True, TEXT)
            self.screen.blit(title, title.get_rect(midtop=(card.centerx, card.y + 30)))
            labels = [("Play as", 84), ("Player name", 174), ("Server address", 244)]
            for label, dy in labels:
                text = self.small_font.render(label, True, MUTED)
                self.screen.blit(text, (card.x + PADDING, card.y + dy))
            for box in self.input_boxes:
                box.draw(self.screen)
            selected = buttons["white" if self.selected_color == "W" else "black"]
            outline = selected.rect.inflate(6, 6)
            pygame.draw.rect(self.screen, ACCENT, outline, 2, border_radius=RADIUS + 3)

        for name, button in buttons.items():
            hovered = button.rect.collidepoint(mouse)
            button.draw(self.screen, self.font_bold, hovered, self.pressed == name)
            if name in ("white", "black"):
                icon = self._picture(name[0] + "K", 32)
                self.screen.blit(icon, button.rect.move(10, 6).topleft)

    def drawPane(self):
        """Draw the side pane with the status, buttons, messages and captures."""
        pygame.draw.rect(self.screen, BACKGROUND, (BOARD, 0, PANE, BOARD))
        x = BOARD + PADDING

        title = self.title_font_small.render("Schrödinger Chess", True, TEXT)
        self.screen.blit(title, (x, PADDING))
        if self.state != "PLAYING":
            mode = "Main menu"
        else:
            mode = "Local game" if self.mode == "LOCAL" else "Online game"
        subtitle = self.small_font.render(mode, True, MUTED)
        self.screen.blit(subtitle, (x, PADDING + 38))

        if self.state == "PLAYING":
            status = pygame.Rect(x, 90, PANE - 2 * PADDING, 60)
            pygame.draw.rect(self.screen, CARD, status, border_radius=RADIUS)
            turn = self._turn()
            if turn is None:
                text, dot = "Waiting for an opponent", MUTED
            else:
                text = ("White" if turn == 0 else "Black") + " to move"
                dot = (245, 245, 245) if turn == 0 else (20, 20, 20)
            center = (status.x + 30, status.centery)
            pygame.draw.circle(self.screen, dot, center, 11)
            pygame.draw.circle(self.screen, BORDER, center, 11, 1)
            label = self.font_bold.render(text, True, TEXT)
            midleft = (status.x + 54, status.centery)
            self.screen.blit(label, label.get_rect(midleft=midleft))

            mouse = pygame.mouse.get_pos()
            for name, button in self._pane_buttons().items():
                hovered = button.rect.collidepoint(mouse)
                button.draw(self.screen, self.font_bold, hovered, self.pressed == name)

        # Message log, the latest message being highlighted
        log = self._log_rect()
        pygame.draw.rect(self.screen, CARD, log, border_radius=RADIUS)
        first = self.current_first_message
        visible = self.message_history[first : first + self._max_messages()]
        line_height = self.small_font.get_linesize()
        for i, message in enumerate(visible):
            latest = first + i == len(self.message_history) - 1
            if first + i in self.error_lines:
                color = ERROR
            else:
                color = TEXT if latest else MUTED
            text = self.small_font.render(message, True, color)
            self.screen.blit(text, (log.x + 12, log.y + 8 + i * line_height))

        # Captured pieces
        y = log.bottom + 14
        self.screen.blit(self.small_font.render("Captured", True, MUTED), (x, y))
        lightBoard = getattr(self.gameEngine, "lightBoard", None)
        if self.state == "PLAYING" and lightBoard is not None:
            size = 30
            for row, color in enumerate([0, 1]):
                for i, piece in enumerate(lightBoard.getDeadPieces(color)):
                    px = x + (i % 10) * size
                    py = y + 26 + row * (size + 8)
                    self.draw_piece(color, piece["natures"], px, py, size)

    def _turn(self):
        """Color of the player to move, or None if the game has not started."""
        if self.mode == "LOCAL" and hasattr(self.gameEngine, "chessBoard"):
            return self.gameEngine.chessBoard.time % 2
        turn = getattr(self.gameEngine, "turn", -1)
        return None if turn == -1 else turn

    def load_images(self):
        """Load the pictures of the pieces."""
        self.pieces_pictures = {}
        for color in "wb":
            for nature in "KQRBNPE":
                path = os.path.join(ASSETS_DIR, "img", color + nature + ".png")
                self.pieces_pictures[color + nature] = pygame.image.load(path)
        self._scaled = {}

    def _picture(self, name, size, alpha=255):
        """Picture of a piece, scaled to ``size`` pixels and cached."""
        key = (name, size, alpha)
        if key not in self._scaled:
            picture = self.pieces_pictures[name]
            if pygame.display.get_surface() is not None:
                picture = picture.convert_alpha()
            picture = pygame.transform.smoothscale(picture, (size, size))
            if alpha < 255:
                picture.set_alpha(alpha)
            self._scaled[key] = picture
        return self._scaled[key]

    def check_address_format(self, s):
        """Check that an address has the form ``host:port``."""
        host, _, port = s.rpartition(":")
        return bool(host) and port.isdigit() and 0 < int(port) <= 65535

    def draw_piece(self, color, natures, x, y, size, extended=False):
        """Draw a piece in a square of the given size.

        A piece with a single nature is drawn normally. A piece with several
        possible natures is drawn as a superposition (elephant) above small
        icons of its possible natures. A piece whose natures are being
        recomputed (``"E"``) is drawn faded.

        :param color: 0 for white, 1 for black.
        :param natures: List of possible natures, or ``"E"`` if unknown.
        :param x: Horizontal position of the top-left corner, in pixels.
        :param y: Vertical position of the top-left corner, in pixels.
        :param size: Size of the square, in pixels.
        :param extended: Ignored, kept for compatibility.
        """
        prefix = "w" if color == 0 else "b"
        x, y, size = int(x), int(y), int(size)
        if natures == "E" or list(natures) == ["E"]:
            self.screen.blit(self._picture(prefix + "E", size, alpha=110), (x, y))
        elif len(natures) == 1:
            self.screen.blit(self._picture(prefix + natures[0], size), (x, y))
        elif size < 40:
            self.screen.blit(self._picture(prefix + "E", size), (x, y))
        else:
            main = int(0.68 * size)
            picture = self._picture(prefix + "E", main)
            self.screen.blit(picture, (x + (size - main) // 2, y + 2))
            small = size // 5
            left = x + (size - small * len(natures)) // 2
            for i, nature in enumerate(natures):
                picture = self._picture(prefix + nature, small)
                self.screen.blit(picture, (left + i * small, y + size - small - 2))
