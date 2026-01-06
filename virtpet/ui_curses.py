import curses

from virtpet.pet import PetState
from virtpet.engine import GameEngine


class CursesUI:
    """
    Terminal UI using curses.

    Responsibilities:
    - Draw the pet and stats
    - Handle keyboard input
    - Provide simple UI-only animation

    Non-responsibilities:
    - Time progression
    - Game logic
    - Persistence
    """

    def __init__(self, engine: GameEngine):
        # Reference to the simulation engine
        self.engine = engine

        # Shortcut to the pet for rendering and input handling
        self.pet = engine.pet

        # --- UI-only animation state ---
        # Horizontal position of the pet emoji
        self._pet_x = 0

        # Direction of movement: 1 = right, -1 = left
        self._pet_dir = 1

    def run(self):
        """
        Entry point for the curses UI.
        """
        curses.wrapper(self._main)

    def _main(self, stdscr):
        """
        Main curses loop.

        `stdscr` = standard screen (curses convention).
        """
        curses.curs_set(0)      # Hide cursor
        stdscr.nodelay(True)    # Non-blocking input
        stdscr.timeout(100)     # Refresh every 100ms

        while self.engine.running:
            self._handle_input(stdscr)
            self._draw(stdscr)

    def _handle_input(self, stdscr):
        """
        Handle non-blocking keyboard input.
        Maps keys to player actions or time control.
        """
        key = stdscr.getch()

        # No key pressed
        if key == -1:
            return

        if key == ord("q"):
            # Quit the application
            self.engine.running = False

        elif key == ord("f"):
            # Feed only if the pet is idle and time is running
            if self.pet.state == PetState.IDLE and not self.pet.paused:
                self.pet.feed()

        elif key == ord("p"):
            # Play only if the pet is idle and time is running
            if self.pet.state == PetState.IDLE and not self.pet.paused:
                self.pet.play()

        elif key == ord("s"):
            # Toggle sleeping state (sleep <-> wake)
            # Sleeping state is preserved across pause/unpause
            self.pet.sleep()

        elif key == ord(" "):
            # Toggle pause without affecting activity state
            # Pause freezes time but keeps the current activity (idle/sleeping)
            self.pet.paused = not self.pet.paused

    def _update_animation(self, max_width: int):
        """
        Update idle animation.
        Moves the pet left/right within the screen bounds.
        """
        if self.pet.state != PetState.IDLE:
            return

        self._pet_x += self._pet_dir

        # Bounce off screen edges
        if self._pet_x <= 0:
            self._pet_x = 0
            self._pet_dir = 1
        elif self._pet_x >= max_width - 2:
            self._pet_x = max_width - 2
            self._pet_dir = -1

    def _draw(self, stdscr):
        """
        Render the entire screen.
        This redraws every frame instead of printing new lines.
        """
        # Layout (content-relative, not terminal-relative)
        pet_y = 10
        footer_y = pet_y + 2

        stdscr.clear()
        height, width = stdscr.getmaxyx()

        # Update animation before drawing
        self._update_animation(width)

        # Compute game clock display
        minutes = self.pet.age
        hours = minutes // 60
        days = hours // 24
        years = days // 365

        # Header
        stdscr.addstr(0, 0, self.pet.name)
        stdscr.addstr(1, 0, f"State: {self.pet.state.value.upper()}")

        # Time
        stdscr.addstr(3, 0, f"Year {years}, Day {days % 365}")
        stdscr.addstr(4, 0, f"Time {hours % 24:02d}:{minutes % 60:02d}")

        # Stats
        stdscr.addstr(6, 0, f"Hunger:     {self.pet.hunger:3}")
        stdscr.addstr(7, 0, f"Energy:     {self.pet.energy:3}")
        stdscr.addstr(8, 0, f"Happiness:  {self.pet.happiness:3}")

        # Pet visual representation
        if self.pet.paused:
            # Pause overlays all activities visually
            stdscr.addstr(pet_y, 0, "⏸️ Paused")
        elif self.pet.state == PetState.SLEEPING:
            stdscr.addstr(pet_y, 0, "😴 Sleeping...")
        else:
            # Idle pet wanders horizontally
            stdscr.addstr(pet_y, self._pet_x, "🐣")

        # Controls footer
        stdscr.addstr(
            footer_y,
            0,
            "[f] Feed  [p] Play  [s] Sleep  [space] Pause  [q] Quit"
        )

        stdscr.refresh()