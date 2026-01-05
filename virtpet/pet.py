class Pet:
    def __init__(self, name: str):
        # Immutable identity (for now)
        self.name = name

        # Time the pet has existed (measured in ticks, not real time)
        self.age = 0

        # Core needs / emotional state (0–100 scale)
        self.hunger = 50      # higher = worse
        self.energy = 50      # higher = better
        self.happiness = 50   # higher = better

    def tick(self):
        """
        Advances the pet's internal state by one unit of time.
        This should be called exactly once per player action.
        """
        self.age += 1

        # Passive decay / growth
        self.hunger = min(100, self.hunger + 5)
        self.energy = max(0, self.energy - 5)

        # Neglect has consequences
        if self.hunger > 80:
            # Severe hunger causes rapid emotional decline
            self.happiness = max(0, self.happiness - 5)
        else:
            # Mild entropy even when things are "fine"
            self.happiness = max(0, self.happiness - 1)

    def feed(self):
        """
        Player action: reduce hunger, small happiness boost.
        """
        self.hunger = max(0, self.hunger - 20)
        self.happiness = min(100, self.happiness + 5)

    def play(self):
        """
        Player action: trades energy for happiness.
        """
        self.energy = max(0, self.energy - 15)
        self.happiness = min(100, self.happiness + 15)

    def sleep(self):
        """
        Player action: restores energy.
        """
        self.energy = min(100, self.energy + 25)

    def to_dict(self) -> dict:
        """
        Serialize the pet into a plain dictionary.
        Safe to save as JSON.
        """
        return {
            "name": self.name,
            "age": self.age,
            "hunger": self.hunger,
            "energy": self.energy,
            "happiness": self.happiness,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Pet":
        """
        Reconstruct a Pet instance from saved data.
        """
        pet = cls(data["name"])
        pet.age = data["age"]
        pet.hunger = data["hunger"]
        pet.energy = data["energy"]
        pet.happiness = data["happiness"]
        return pet
