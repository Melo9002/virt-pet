import curses
import textwrap

from virtpet.engine import GameEngine
from virtpet.sprites import pet_art


def _conversation_lines(messages, width: int = 56,
                        max_lines: int = 3) -> list[str]:
    """Wrap complete recent messages into the small conversation window."""
    selected: list[list[str]] = []
    remaining = max_lines
    for message in reversed(list(messages)):
        wrapped = textwrap.wrap(
            f"{message.speaker}: {message.text}",
            width=width,
            subsequent_indent="  ",
        ) or [f"{message.speaker}:"]
        if len(wrapped) > remaining:
            if not selected:
                selected.append(wrapped[:remaining])
            break
        selected.append(wrapped)
        remaining -= len(wrapped)
        if remaining == 0:
            break
    return [line for group in reversed(selected) for line in group]


class CursesUI:
    MIN_HEIGHT = 27
    MIN_WIDTH = 64
    ROOM_WIDTH = 76

    def __init__(self, engine: GameEngine):
        self.engine = engine
        self.pet = engine.pet
        self._frame = 0
        self._colors = False
        self._chatting = False
        self._chat_buffer = ""
        self._reaction: tuple[str, int] | None = None

    def run(self) -> None:
        curses.wrapper(self._main_loop)

    def _main_loop(self, screen) -> None:
        self._configure(screen)
        while self.engine.running:
            self._handle_input(screen, screen.getch())
            self.engine.update()
            self._draw(screen)
            self._frame += 1

    def _configure(self, screen) -> None:
        try:
            curses.curs_set(0)
        except curses.error:
            pass
        screen.timeout(100)
        screen.keypad(True)
        if curses.has_colors():
            try:
                curses.start_color()
                curses.use_default_colors()
                curses.init_pair(1, curses.COLOR_CYAN, -1)
                curses.init_pair(2, curses.COLOR_GREEN, -1)
                curses.init_pair(3, curses.COLOR_YELLOW, -1)
                curses.init_pair(4, curses.COLOR_RED, -1)
                curses.init_pair(5, curses.COLOR_MAGENTA, -1)
                self._colors = True
            except curses.error:
                self._colors = False

    def _color(self, pair: int) -> int:
        return curses.color_pair(pair) if self._colors else 0

    def _handle_input(self, screen, key: int) -> None:
        if self._chatting:
            if key in (10, 13, curses.KEY_ENTER):
                message = self._chat_buffer
                self._chat_buffer = ""
                self._set_chat_mode(screen, False)
                if message.strip():
                    self.engine.log(f"{self.pet.name} is thinking...")
                    self._draw(screen)
                    self.engine.talk(message)
            elif key == 27:
                self._chat_buffer = ""
                self._set_chat_mode(screen, False)
            elif key in (curses.KEY_BACKSPACE, 8, 127):
                self._chat_buffer = self._chat_buffer[:-1]
            elif 32 <= key <= 126 and len(self._chat_buffer) < 160:
                self._chat_buffer += chr(key)
            return
        if key in (ord("q"), ord("Q")):
            self.engine.stop()
        elif key in (ord("f"), ord("F")):
            self._react("feed", self.engine.feed())
        elif key in (ord("p"), ord("P")):
            self._react("play", self.engine.play())
        elif key in (ord("s"), ord("S")):
            self.engine.toggle_sleep()
        elif key in (ord("t"), ord("T")):
            self._react("tidy", self.engine.flush())
        elif key == ord(" "):
            self.engine.toggle_pause()
        elif key in (ord("c"), ord("C")):
            self._set_chat_mode(screen, True)

    def _set_chat_mode(self, screen, enabled: bool) -> None:
        self._chatting = enabled
        try:
            curses.curs_set(1 if enabled else 0)
        except curses.error:
            pass

    def _react(self, action: str, succeeded: bool) -> None:
        if succeeded:
            self._reaction = (action, self._frame)

    def _put(self, screen, y: int, x: int, text: str, attr: int = 0) -> None:
        height, width = screen.getmaxyx()
        if 0 <= y < height and 0 <= x < width - 1:
            try:
                screen.addnstr(y, x, text, width - x - 1, attr)
            except curses.error:
                pass

    def _meter(self, value: int, good_high: bool = True) -> tuple[str, int]:
        filled = round(value / 10)
        meter = "[" + "#" * filled + "." * (10 - filled) + "]"
        healthy = value >= 60 if good_high else value <= 40
        warning = 30 <= value < 60 if good_high else 40 < value < 75
        color = 2 if healthy else (3 if warning else 4)
        return meter, self._color(color)

    def _draw(self, screen) -> None:
        screen.erase()
        height, width = screen.getmaxyx()
        if height < self.MIN_HEIGHT or width < self.MIN_WIDTH:
            self._put(screen, 0, 0, "This little home needs more room!", curses.A_BOLD)
            self._put(screen, 2, 0, f"Resize to at least {self.MIN_WIDTH} x {self.MIN_HEIGHT}.")
            self._put(screen, 4, 0, "[q] quit")
            screen.refresh()
            return

        home_width = self.ROOM_WIDTH if width >= self.ROOM_WIDTH else self.MIN_WIDTH
        expanded = home_width == self.ROOM_WIDTH
        left = max(0, (width - home_width) // 2)
        inner = home_width - 2
        safe_name = self.pet.name[:32]
        title = f" {safe_name}'s tiny home "
        self._put(screen, 0, left, "+" + "-" * inner + "+", self._color(1))
        self._put(screen, 0, left + (home_width - len(title)) // 2, title,
                  self._color(1) | curses.A_BOLD)
        for row in range(1, 23):
            self._put(screen, row, left, "|" + " " * inner + "|", self._color(1))
        self._put(screen, 23, left, "+" + "-" * inner + "+", self._color(1))

        status = "PAUSED" if self.pet.paused else self.pet.state.value.upper()
        if self.engine.minutes_per_real_second != 1.0:
            status += f"  DEBUG x{self.engine.minutes_per_real_second:g}"
        self._put(screen, 2, left + 3, f"{self.engine.get_local_time()}  {status}", curses.A_BOLD)
        age_x = 52 if expanded else 42
        self._put(screen, 2, left + age_x, f"age {self.pet.age // 60}h {self.pet.age % 60:02}m")
        self._put(screen, 3, left + 3, f"voice: {self.engine.voice_status}", curses.A_DIM)
        if expanded:
            self._draw_room(screen, left)
        else:
            self._draw_pet(screen, left + 7)
        self._draw_reaction(screen, left, expanded)

        care_x = 43 if expanded else 35
        self._put(screen, 4, left + care_x, "CARE", curses.A_BOLD | self._color(5))
        stats = [("Hunger", self.pet.hunger, False),
                 ("Joy", self.pet.happiness, True),
                 ("Mess", self.pet.toilet, False),
                 ("Tired", self.pet.tiredness, False)]
        for index, (label, value, good_high) in enumerate(stats):
            meter, color = self._meter(value, good_high)
            self._put(screen, 6 + index * 2, left + care_x, f"{label:<7} {meter} {value:3}", color)
        self._put(screen, 14, left + care_x, f"State: {self.pet.condition.value}", curses.A_BOLD)

        self._put(screen, 15, left + 3, "CONVERSATION", curses.A_BOLD | self._color(5))
        lines = _conversation_lines(self.engine.conversation, width=home_width - 8)
        if lines:
            for index, line in enumerate(lines):
                self._put(screen, 16 + index, left + 3, line)
        else:
            self._put(screen, 16, left + 3, f"{self.pet.name} is listening...", curses.A_DIM)

        self._put(screen, 20, left + 3, "LATEST", curses.A_BOLD | self._color(5))
        if self.engine.events:
            self._put(screen, 21, left + 3,
                      f"> {self.engine.events[0]}"[:home_width - 7])

        if self._chatting:
            prompt = f"Say (Enter sends, Esc cancels): {self._chat_buffer}"
            self._put(screen, 25, left, prompt[:62], curses.A_BOLD)
            try:
                screen.move(25, min(width - 2, left + len(prompt[:62])))
            except curses.error:
                pass
        else:
            first = "[C] chat  [F] feed  [P] play  [S] sleep/wake"
            second = "[T] tidy  [space] pause  [Q] save & quit"
            self._put(screen, 24, max(0, (width - len(first)) // 2), first, curses.A_DIM)
            self._put(screen, 25, max(0, (width - len(second)) // 2), second, curses.A_DIM)
        screen.refresh()

    def _draw_pet(self, screen, x: int) -> None:
        art = pet_art(self.pet.condition, self.pet.state, self._frame,
                      paused=self.pet.paused)
        for row, line in enumerate(art):
            self._put(screen, 6 + row, x, line, curses.A_BOLD | self._color(3))
        if self.pet.paused:
            self._put(screen, 11, x + 2, "[pause]", curses.A_DIM)

    def _draw_room(self, screen, left: int) -> None:
        """Draw the wider diorama without affecting compact terminals."""
        try:
            hour = int(self.engine.get_local_time().split(":", 1)[0])
        except (ValueError, IndexError):
            hour = 12
        if 6 <= hour < 18:
            window = (".-----.", "| \\|/ |", "| -O- |", "'-----'")
        else:
            window = (".-----.", "| * . |", "|  .  |", "'-----'")
        for row, line in enumerate(window):
            self._put(screen, 5 + row, left + 3, line, self._color(1))

        self._draw_pet(screen, left + 13)
        furniture = ((8, 28, "  ____"), (9, 28, " /___/|"),
                     (10, 28, " |___||"))
        for row, x, line in furniture:
            self._put(screen, row, left + x, line, curses.A_DIM | self._color(3))

    def _draw_reaction(self, screen, left: int, expanded: bool) -> None:
        if self._reaction is None:
            return
        action, started = self._reaction
        elapsed = self._frame - started
        if elapsed >= 14:
            self._reaction = None
            return

        pet_x = left + (13 if expanded else 7)
        if action == "feed":
            crumb = "." if (elapsed // 2) % 2 else "*"
            self._put(screen, 10, pet_x + 9, crumb, self._color(3))
            self._put(screen, 11, pet_x + 7, "(___)", self._color(3))
        elif action == "play":
            travel = elapsed if elapsed < 7 else 13 - elapsed
            self._put(screen, 11 - (travel % 3 == 1), left + 3 + travel * 3,
                      "o", curses.A_BOLD | self._color(5))
        elif action == "tidy":
            sparkle = "*" if (elapsed // 2) % 2 else "+"
            self._put(screen, 7, pet_x + 12, sparkle, self._color(1))
            self._put(screen, 8, pet_x + 10, "\\|", self._color(3))
            self._put(screen, 9, pet_x + 11, "\\", self._color(3))
