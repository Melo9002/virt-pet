from enum import Enum


class PetState(Enum):
    IDLE = "idle"
    SLEEPING = "sleeping"


class Pet:
    def __init__(self, name: str):
        # Identity
        self.name = name

        # What the pet is currently doing
        self.state = PetState.IDLE

        # Whether time progression is paused
        # Pause is a modifier, not an activity
        self.paused = False

        # Age in in-game minutes
        self.age = 0

        # Core needs / emotional state (0–100 scale)
        # Hunger: higher = worse
        # Energy / Happiness: higher = better
        self.hunger = 50
        self.energy = 50
        self.happiness = 50

    def tick(self, minutes: int = 1):
        """
        Advance the pet by a number of in-game minutes.

        This method is:
        - time-driven
        - UI-agnostic
        - the only place where passive state changes occur
        """

        # Paused freezes time entirely, regardless of activity
        if self.paused:
            return

        for _ in range(minutes):
            self.age += 1

            if self.state == PetState.SLEEPING:
                # Sleeping behavior:
                # - Energy recovers
                # - Hunger still increases slowly
                # - No happiness decay (restful state)
                self.energy = min(100, self.energy + 2)
                self.hunger = min(100, self.hunger + 1)
                continue

            # IDLE behavior
            self.hunger = min(100, self.hunger + 1)
            self.energy = max(0, self.energy - 1)

            # Emotional impact of hunger
            if self.hunger > 80:
                self.happiness = max(0, self.happiness - 2)

    def feed(self):
        """
        Player action: reduce hunger, small happiness boost.
        Valid only while IDLE (enforced by UI).
        """
        self.hunger = max(0, self.hunger - 20)
        self.happiness = min(100, self.happiness + 5)

    def play(self):
        """
        Player action: trade energy for happiness.
        """
        self.energy = max(0, self.energy - 15)
        self.happiness = min(100, self.happiness + 15)

    def sleep(self):
        """
        Toggle sleeping state.
        """
        if self.state == PetState.SLEEPING:
            self.state = PetState.IDLE
        else:
            self.state = PetState.SLEEPING

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

        # Restore activity state (default to IDLE)
        pet.state = PetState(data.get("state", PetState.IDLE.value))

        # Restore pause flag (default to False for older saves)
        pet.paused = data.get("paused", False)

        return pet