import time
from collections import deque
from datetime import datetime
from typing import Callable

from virtpet.persistence import save_pet
from virtpet.pet import Pet, PetState
from virtpet.voice import ChatMessage, FallbackVoice, PetVoice


class GameEngine:
    """Translate elapsed real time and player intent into pet changes."""

    def __init__(self, pet: Pet, minutes_per_real_second: float = 1.0,
                 voice: PetVoice | None = None, *,
                 clock: Callable[[], float] = time.monotonic,
                 saver: Callable[[Pet], None] = save_pet):
        self.pet = pet
        self.minutes_per_real_second = minutes_per_real_second
        self.running = True
        self.events: deque[str] = deque(maxlen=4)
        self.conversation: deque[ChatMessage] = deque(maxlen=8)
        self.voice = voice or FallbackVoice()
        self._clock = clock
        self._save = saver
        self._last_time = self._clock()
        self._accumulated_minutes = 0.0
        self.log(f"{pet.name} is {pet.mood}.")

    def update(self) -> None:
        now = self._clock()
        delta = max(0.0, now - self._last_time)
        self._last_time = now
        if self.pet.paused:
            return
        self._accumulated_minutes += delta * self.minutes_per_real_second
        whole_minutes = int(self._accumulated_minutes)
        if whole_minutes:
            self.pet.tick(whole_minutes)
            self._accumulated_minutes -= whole_minutes
            self._save(self.pet)

    def log(self, message: str) -> None:
        self.events.appendleft(message)

    def _act(self, action, success: str, blocked: str) -> None:
        if action():
            self.log(success)
            self._save(self.pet)
        else:
            self.log(blocked)

    def feed(self) -> None:
        self._act(self.pet.feed, f"You shared a tasty snack with {self.pet.name}.",
                  "Snacks must wait until everyone is awake.")

    def play(self) -> None:
        self._act(self.pet.play, f"You and {self.pet.name} played together!",
                  "Playtime must wait until everyone is awake.")

    def flush(self) -> None:
        self._act(self.pet.flush, "Everything is fresh and tidy again.",
                  "Time is paused; cleaning can wait.")

    def toggle_sleep(self) -> None:
        was_sleeping = self.pet.state == PetState.SLEEPING
        self._act(self.pet.toggle_sleep,
                  f"{self.pet.name} {'woke up.' if was_sleeping else 'curled up to sleep.'}",
                  "Unpause before changing the routine.")

    def toggle_pause(self) -> None:
        self.pet.paused = not self.pet.paused
        self._last_time = self._clock()
        self.log("Time is paused." if self.pet.paused else "Time is moving again.")
        self._save(self.pet)

    def talk(self, message: str) -> str | None:
        """Send text to the configured voice and retain a short chat context."""
        message = " ".join(message.strip().split())[:160]
        if not message:
            return None
        history = tuple(self.conversation)
        self.conversation.append(ChatMessage("you", message))
        response = self.voice.reply(self.pet, message, history)
        self.conversation.append(ChatMessage(self.pet.name, response))
        return response

    def stop(self) -> None:
        self.running = False
        self._save(self.pet)

    def get_local_time(self) -> str:
        return datetime.now().strftime("%H:%M")
