import time
from virtpet.pet import Pet
from virtpet.persistence import save_pet
from collections import deque
from datetime import datetime


class GameEngine:
    """
    Time-driven simulation engine.

    Responsibilities:
    - Track real time
    - Convert real time into in-game minutes
    - Advance the pet simulation
    - Trigger persistence
    - Control the main loop lifecycle

    This class does NOT:
    - Handle input
    - Render UI
    - Contain pet logic
    """

    # -----------------------------
    # Construction & Configuration
    # -----------------------------

    def __init__(self, pet: Pet, minutes_per_real_second: float = 1.0):
        """
        :param pet: The Pet instance being simulated
        :param minutes_per_real_second: How many in-game minutes pass per real second
        """
        # Core domain object
        self.pet: Pet = pet

        # Time scaling factor
        self.minutes_per_real_second: float = minutes_per_real_second

        # Main loop control flag
        self.running: bool = True

        #logs
        self.events = deque(maxlen=5)

        # -----------------------------
        # Internal time tracking
        # -----------------------------

        # Last real-world timestamp (seconds)
        self._last_time: float = time.time()

        # Fractional in-game minutes accumulated
        self._accumulated_minutes: float = 0.0

    # -----------------------------
    # Main Loop
    # -----------------------------

    def run(self) -> None:
        """
        Main simulation loop.

        This loop:
        - Measures real time delta
        - Converts it to in-game time
        - Advances the pet in whole-minute steps
        - Persists state after each advancement
        """
        while self.running:
            self._update_sleep_state()
            self._update_time()
            time.sleep(0.05)

    # -----------------------------
    # Internal Helpers
    # -----------------------------

    # Constant for now Sleep window (local time)
    SLEEP_START_HOUR = 22  # 10 PM
    SLEEP_END_HOUR = 6  # 6 AM

    def _is_sleep_time(self) -> bool:
        now = datetime.now()
        hour = now.hour

        # Night crosses midnight
        return hour >= self.SLEEP_START_HOUR or hour < self.SLEEP_END_HOUR

    def _update_time(self) -> None:
        """
        Update accumulated in-game time and advance the simulation
        in whole-minute increments.
        """
        now = time.time()
        delta_seconds = now - self._last_time
        self._last_time = now

        # Convert real time delta to in-game minutes
        self._accumulated_minutes += (
            delta_seconds * self.minutes_per_real_second
        )

        # Only advance whole in-game minutes
        whole_minutes = int(self._accumulated_minutes)

        if whole_minutes > 0:
            self.pet.tick(whole_minutes)
            self._accumulated_minutes -= whole_minutes

            # Persist after state changes
            save_pet(self.pet)

    def log(self, message: str) -> None:
        """
        Add a semantic event to the event log.
        """
        self.events.append(message)

    """
    Actions.
    """
    def feed(self) -> None:
        if self.pet.state != self.pet.state.IDLE:
            return
        self.pet.feed()
        self.log(f"[CARE] You fed {self.pet.name}.")

    def flush(self) -> None:
        self.pet.flush()
        self.log(f"[HYGIENE] You cleaned up after {self.pet.name}.")

    def toggle_sleep(self) -> None:
        was_sleeping = self.pet.state == self.pet.state.SLEEPING
        self.pet.sleep()
        if was_sleeping:
            self.log(f"[REST] You woke {self.pet.name} up.")
        else:
            self.log(f"[REST] You put {self.pet.name} to rest.")

    def play(self):
        self.pet.play()
        self.log(f"[PLAY] You played with {self.pet.name}.")

    #pause button
    def toggle_pause(self) -> None:
        """
        Toggle simulation pause.

        NOTE:
        Pause is currently implemented as a flag on the Pet.
        In the future, pause may be handled entirely by the engine
        by skipping tick() calls.
        """
        self.pet.paused = not self.pet.paused

    def _update_sleep_state(self) -> None:
        """
        Enforce sleep state based on real-world time.
        """
        should_sleep = self._is_sleep_time()

        if should_sleep and self.pet.state != self.pet.state.SLEEPING:
            self.pet.sleep()
            self.log(f"[REST] {self.pet.name} fell asleep.")

        elif not should_sleep and self.pet.state == self.pet.state.SLEEPING:
            self.pet.sleep()
            self.log(f"[REST] {self.pet.name} woke up.")
