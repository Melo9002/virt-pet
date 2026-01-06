import curses

from virtpet.pet import PetState
from virtpet.engine import GameEngine


class CursesUI:
    """
    Terminal-based UI implemented using curses.

    Responsibilities:
    - Render pet state and stats
    - Handle keyboard input
    - Maintain UI-only animation state

    Non-responsibilities:
    - Game logic
    - Time progression
    - Persistence
    """

    # -----------------------------
    # Construction
    # -----------------------------

    def __init__(self, engine: GameEngine):
        # Reference to the simulation engine
        self.engine: GameEngine = engine

        # Shortcut to the pet (read-only usage expected)
        self.pet = engine.pet

        # -----------------------------
        # UI-only animation state
        # -----------------------------

        # Horizontal position of the pet sprite
        self._pet_x: int = 0

        # Horizontal movement direction (1 = right, -1 = left)
        self._pet_dir: int = 1

        # UI-only poop positions (cosmetic)
        self._poops: list[tuple[int, int]] = []

    # -----------------------------
    # Public API
    # -----------------------------

    def run(self) -> None:
        """
        Entry point for the curses UI.
        """
        curses.wrapper(self._main_loop)

    # -----------------------------
    # Main Loop
    # -----------------------------

    def _main_loop(self, stdscr) -> None:
        """
        Main curses loop.

        This method:
        - Configures curses
        - Runs the input/render loop
        """
        self._configure_curses(stdscr)

        while self.engine.running:
            self._handle_input(stdscr)
            self._draw_frame(stdscr)

    def _configure_curses(self, stdscr) -> None:
        """
        One-time curses configuration.
        """
        curses.curs_set(0)      # Hide cursor
        stdscr.nodelay(True)    # Non-blocking input
        stdscr.timeout(100)     # Refresh every 100ms

    # -----------------------------
    # Input Handling
    # -----------------------------

    def _handle_input(self, stdscr) -> None:
        """
        Handle non-blocking keyboard input.
        Maps keys to pet actions or time control.
        """
        key = stdscr.getch()

        if key == -1:
            return

        if key == ord("q"):
            self.engine.running = False

        elif key == ord("f"):
            self._handle_feed()

        elif key == ord("p"):
            self._handle_play()

        elif key == ord("s"):
            self.pet.sleep()

        elif key == ord("t"):
            self._handle_flush()

        elif key == ord(" "):
            # Pause toggles time without changing activity
            self.pet.paused = not self.pet.paused

    def _handle_feed(self) -> None:
        if self.pet.state == PetState.IDLE and not self.pet.paused:
            self.pet.feed()

    def _handle_play(self) -> None:
        if self.pet.state == PetState.IDLE and not self.pet.paused:
            self.pet.play()

    def _handle_flush(self) -> None:
        if not self.pet.paused:
            self.pet.flush()
            self._clear_poop()

    # -----------------------------
    # Animation
    # -----------------------------

    def _update_animation(self, screen_width: int) -> None:
        """
        Update idle animation.

        Moves the pet horizontally while idle.
        """
        if self.pet.state != PetState.IDLE:
            return

        self._pet_x += self._pet_dir

        if self._pet_x <= 0:
            self._pet_x = 0
            self._pet_dir = 1
        elif self._pet_x >= screen_width - 2:
            self._pet_x = screen_width - 2
            self._pet_dir = -1

    # -----------------------------
    # Rendering
    # -----------------------------

    def _draw_frame(self, stdscr) -> None:
        """
        Render a single frame.
        """
        stdscr.clear()

        height, width = stdscr.getmaxyx()
        self._update_animation(width)

        self._draw_header(stdscr)
        self._draw_time(stdscr)
        self._draw_stats(stdscr)
        self._draw_poops(stdscr)
        self._draw_pet(stdscr)
        self._draw_footer(stdscr)

        stdscr.refresh()

    def _draw_header(self, stdscr) -> None:
        stdscr.addstr(0, 0, self.pet.name)
        stdscr.addstr(1, 0, f"State: {self.pet.state.value.upper()}")

    def _draw_time(self, stdscr) -> None:
        minutes = self.pet.age
        hours = minutes // 60
        days = hours // 24
        years = days // 365

        stdscr.addstr(3, 0, f"Year {years}, Day {days % 365}")
        stdscr.addstr(4, 0, f"Time {hours % 24:02d}:{minutes % 60:02d}")

    def _draw_stats(self, stdscr) -> None:
        stdscr.addstr(6, 0, f"Hunger:     {self.pet.hunger:3}")
        stdscr.addstr(7, 0, f"Energy:     {self.pet.energy:3}")
        stdscr.addstr(8, 0, f"Happiness:  {self.pet.happiness:3}")
        stdscr.addstr(9, 0, f"Toilet:     {self.pet.toilet:3}")

    def _draw_poops(self, stdscr) -> None:
        for y, x in self._poops:
            stdscr.addstr(y, x, "💩")

    def _clear_poop(self) -> None:
        self._poops.clear()

    def _draw_pet(self, stdscr) -> None:
        pet_y = 10
        """
        Poop position
        """
        expected_poops = self.pet.toilet // 20
        while len(self._poops) < expected_poops:
            self._poops.append((pet_y, self._pet_x))
        """
        Poop position
        """
        if self.pet.paused:
            stdscr.addstr(pet_y, 0, "⏸️ Paused")
        elif self.pet.state == PetState.SLEEPING:
            stdscr.addstr(pet_y, 0, "😴 Sleeping...")
        else:
            stdscr.addstr(pet_y, self._pet_x, "🐣")

    def _draw_footer(self, stdscr) -> None:
        stdscr.addstr(
            12,
            0,
            "[f] Feed  [p] Play  [s] Sleep  [t] Flush  [space] Pause  [q] Quit"
        )
