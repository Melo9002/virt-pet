import curses
from virtpet.pet import Pet, PetState
from virtpet.engine import GameEngine

class CursesUI:
    def __init__(self, engine: GameEngine):
        self.engine = engine # Reference to the simulation engine
        self.pet = engine.pet # Shortcut to the pet for rendering and input handling

        # --- UI-only animation state ---
        # Horizontal position of the pet emoji
        self._pet_x = 0

        # Direction of movement: 1 = right, -1 = left
        self._pet_dir = 1

    def run(self):
        curses.wrapper(self._main)

    def _main(self, stdscr):
        # Curses setup
        curses.curs_set(0)          # hide cursor
        stdscr.nodelay(True)        # non-blocking input
        stdscr.timeout(100)         # refresh every 100ms

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
        Update pet position for idle animation.
        Called once per frame.
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
        PET_Y = 10
        FOOTER_Y = PET_Y + 2

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
        stdscr.addstr(0, 0, f"{self.pet.name}")
        stdscr.addstr(1, 0, f"State: {self.pet.state.value.upper()}")

        stdscr.addstr(3, 0, f"Year {years}, Day {days % 365}")
        stdscr.addstr(4, 0, f"Time {hours % 24:02d}:{minutes % 60:02d}")

        # Stats
        stdscr.addstr(6, 0, f"Hunger:     {self.pet.hunger:3}")
        stdscr.addstr(7, 0, f"Energy:     {self.pet.energy:3}")
        stdscr.addstr(8, 0, f"Happiness:  {self.pet.happiness:3}")

        # Pet visual representation
        if self.pet.paused:
            # Sleeping or paused pet stays still
            stdscr.addstr(PET_Y, 0, "⏸️ Paused")
        elif self.pet.state == PetState.SLEEPING:
            stdscr.addstr(PET_Y, 0, "😴 Sleeping...")
        else:
            # Idle pet wanders horizontally
            stdscr.addstr(10, self._pet_x, "🐣")

        # Controls footer
        stdscr.addstr(
            FOOTER_Y,
            0,
            "[f] Feed  [p] Play  [s] Sleep  [space] Pause  [q] Quit"
        )

        stdscr.refresh()
