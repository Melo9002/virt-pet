from enum import Enum
import random


class PetState(Enum):
    """
    Activity state of the pet.
    This represents what the pet is doing, not time control.
    """
    IDLE = "idle"
    SLEEPING = "sleeping"


class Pet:
    """
    Core domain object representing the virtual pet.

    Responsibilities:
    - Own all pet state (needs, age, activity)
    - Define how time affects the pet (tick)
    - Define player actions (feed, play, sleep, flush)
    - Serialize / deserialize itself for persistence

    This class is UI-agnostic and engine-agnostic.
    """

    # -----------------------------
    # Construction & Identity
    # -----------------------------

    def __init__(self, name: str):
        # Identity
        self.name: str = name

        # Activity state (what the pet is doing)
        self.state: PetState = PetState.IDLE

        # Time control flag
        # Pause freezes time but does NOT change activity
        self.paused: bool = False

        # Age in in-game minutes
        self.age: int = 0

        # -----------------------------
        # Core needs (0–100 scale)
        # -----------------------------
        # Hunger: higher = worse
        # Energy / Happiness: higher = better
        # Toilet: higher = worse (must be flushed)
        self.hunger: int = 50
        self.energy: int = 50
        self.happiness: int = 50
        self.toilet: int = 0

    # -----------------------------
    # Time Progression
    # -----------------------------

    def tick(self, minutes: int = 1) -> None:
        """
        Advance the pet by a number of in-game minutes.

        Rules:
        - This is the ONLY place where passive changes occur
        - UI and engine must call this, never mutate needs directly
        """

        # Paused freezes time entirely, regardless of activity
        if self.paused:
            return

        for _ in range(minutes):
            self.age += 1

            # -------------------------
            # Passive need progression
            # -------------------------

            # Hunger and toilet always increase over time
            self.hunger = min(100, self.hunger + 1)
            self.toilet = min(100, self.toilet + 1)

            if self.state == PetState.SLEEPING:
                # Sleeping behavior:
                # - Energy recovers
                # - Reduced penalties
                self.energy = min(100, self.energy + 2)
            else:
                # IDLE behavior
                self.energy = max(0, self.energy - 1)

            # -------------------------
            # Happiness decay
            # -------------------------

            # Base emotional entropy (always on)
            base_decay = random.randint(0, 3)
            self.happiness = max(0, self.happiness - base_decay)

            # Severe neglect penalty
            if self.hunger == 100 or self.toilet == 100:
                self.happiness = max(0, self.happiness - 10)

    # -----------------------------
    # Player Actions
    # -----------------------------

    def feed(self) -> None:
        """
        Player action: reduce hunger, small happiness boost.
        Valid only while IDLE (enforced by UI).
        """
        self.hunger = max(0, self.hunger - 20)
        self.happiness = min(100, self.happiness + 5)
        self.toilet = min(100, self.toilet + 5)

    def play(self) -> None:
        """
        Player action: trade energy for happiness.
        """
        self.energy = max(0, self.energy - 15)
        self.happiness = min(100, self.happiness + 15)

    def sleep(self) -> None:
        """
        Toggle sleeping state.
        """
        if self.state == PetState.SLEEPING:
            self.state = PetState.IDLE
        else:
            self.state = PetState.SLEEPING

    def flush(self) -> None:
        """
        Player action: reset toilet need.
        This is a hard reset, unlike other needs.
        """
        self.toilet = 0

    # -----------------------------
    # Persistence
    # -----------------------------

    def to_dict(self) -> dict:
        """
        Serialize the pet into a JSON-safe dictionary.
        This is the single source of truth for persistence.
        """
        return {
            "name": self.name,
            "age": self.age,
            "hunger": self.hunger,
            "energy": self.energy,
            "happiness": self.happiness,
            "toilet": self.toilet,
            # Persist activity state to preserve intent
            "state": self.state.value,
            # Persist pause so time-control survives reloads
            "paused": self.paused,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Pet":
        """
        Reconstruct a Pet instance from saved data.
        Backward-compatible with older save files.
        """
        pet = cls(data["name"])

        pet.age = data["age"]
        pet.hunger = data["hunger"]
        pet.energy = data["energy"]
        pet.happiness = data["happiness"]
        pet.toilet = data.get("toilet", 0)

        # Restore activity state (default to IDLE)
        pet.state = PetState(data.get("state", PetState.IDLE.value))

        # Restore pause flag (default to False)
        pet.paused = data.get("paused", False)

        return pet
