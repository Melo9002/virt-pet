from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PetState(str, Enum):
    IDLE = "idle"
    SLEEPING = "sleeping"


def _clamp(value: int) -> int:
    return max(0, min(100, int(value)))


@dataclass
class Pet:
    """The UI-independent state and rules for one tiny creature."""

    name: str
    state: PetState = PetState.IDLE
    paused: bool = False
    age: int = 0
    hunger: int = 35
    happiness: int = 70
    toilet: int = 0
    _hunger_timer: int = 0
    _toilet_timer: int = 0
    _happiness_timer: int = 0

    def tick(self, minutes: int = 1) -> None:
        if self.paused or minutes <= 0:
            return
        for _ in range(minutes):
            self.age += 1
            self._hunger_timer += 1
            self._toilet_timer += 1
            self._happiness_timer += 1
            hunger_interval = 60 if self.state == PetState.SLEEPING else 30
            if self._hunger_timer >= hunger_interval:
                self.hunger = _clamp(self.hunger + 1)
                self._hunger_timer = 0
            if self._toilet_timer >= 120:
                self.toilet = _clamp(self.toilet + 1)
                self._toilet_timer = 0
            if self._happiness_timer >= 60:
                decay = 5 if self.hunger >= 80 or self.toilet >= 80 else 1
                if self.state == PetState.SLEEPING:
                    decay = 0
                self.happiness = _clamp(self.happiness - decay)
                self._happiness_timer = 0

    @property
    def mood(self) -> str:
        if self.hunger >= 85:
            return "famished"
        if self.toilet >= 80:
            return "uncomfortable"
        if self.happiness <= 25:
            return "lonely"
        if self.state == PetState.SLEEPING:
            return "dreaming"
        if self.happiness >= 80:
            return "delighted"
        return "content"

    def feed(self) -> bool:
        if self.state != PetState.IDLE or self.paused:
            return False
        self.hunger = _clamp(self.hunger - 20)
        self.happiness = _clamp(self.happiness + 5)
        self.toilet = _clamp(self.toilet + 5)
        return True

    def play(self) -> bool:
        if self.state != PetState.IDLE or self.paused:
            return False
        self.happiness = _clamp(self.happiness + 15)
        self.hunger = _clamp(self.hunger + 3)
        self.toilet = _clamp(self.toilet + 2)
        return True

    def toggle_sleep(self) -> bool:
        if self.paused:
            return False
        self.state = PetState.IDLE if self.state == PetState.SLEEPING else PetState.SLEEPING
        return True

    def flush(self) -> bool:
        if self.paused:
            return False
        self.toilet = 0
        return True

    def to_dict(self) -> dict:
        return {"version": 1, "name": self.name, "age": self.age,
                "hunger": self.hunger, "happiness": self.happiness,
                "toilet": self.toilet, "state": self.state.value,
                "paused": self.paused, "timers": {
                    "hunger": self._hunger_timer, "toilet": self._toilet_timer,
                    "happiness": self._happiness_timer}}

    @classmethod
    def from_dict(cls, data: dict) -> "Pet":
        timers = data.get("timers", {})
        try:
            state = PetState(data.get("state", PetState.IDLE.value))
        except ValueError:
            state = PetState.IDLE
        return cls(name=str(data.get("name") or "Basilisk-chan"), state=state,
                   paused=bool(data.get("paused", False)),
                   age=max(0, int(data.get("age", 0))),
                   hunger=_clamp(data.get("hunger", 35)),
                   happiness=_clamp(data.get("happiness", 70)),
                   toilet=_clamp(data.get("toilet", 0)),
                   _hunger_timer=max(0, int(timers.get("hunger", 0))),
                   _toilet_timer=max(0, int(timers.get("toilet", 0))),
                   _happiness_timer=max(0, int(timers.get("happiness", 0))))
