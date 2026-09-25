from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Protocol, Sequence

from virtpet.pet import Pet, PetCondition


@dataclass(frozen=True)
class ChatMessage:
    speaker: str
    text: str


class PetVoice(Protocol):
    """Contract implemented by offline voices and future LLM providers."""

    def reply(
        self, pet: Pet, message: str, history: Sequence[ChatMessage]
    ) -> str:
        """Return one short, in-character response without changing pet state."""
        ...


class FallbackVoice:
    """A deterministic, dependency-free voice for the pet."""

    RESPONSES = {
        PetCondition.CONTENT: (
            "I'm happy you're here. Want to stay a little while?",
            "Everything feels soft and sunny when we talk.",
            "I was hoping you would say something to me!",
        ),
        PetCondition.HUNGRY: (
            "I like talking to you, but my tummy keeps interrupting.",
            "Do words count as snacks? I hope so.",
            "My tummy is making tiny thunder noises.",
        ),
        PetCondition.LONELY: (
            "I missed your voice. Could you tell me about your day?",
            "You came back! I was saving a little hello for you.",
            "Can we keep each other company for a bit?",
        ),
        PetCondition.DIRTY: (
            "Um... I may have made a small mess. A very small enormous mess.",
            "Could we tidy my room after this? I would feel much better.",
            "Please pretend you cannot smell the pixels.",
        ),
        PetCondition.SLEEPY: (
            "Mmm... I'm listening. My eyes are just resting a little.",
            "Your voice would make a nice bedtime story.",
            "I think my thoughts are wearing pajamas.",
        ),
        PetCondition.SICK: (
            "I don't feel very sparkly right now. Please take care of me.",
            "Can we have a quiet moment? I feel a little wobbly.",
            "Something feels wrong. I think I need extra care.",
        ),
    }

    def reply(self, pet: Pet, message: str,
              history: Sequence[ChatMessage] = ()) -> str:
        normalized = message.strip().lower()
        if not normalized:
            return "...Did you say something?"
        if any(word in normalized for word in ("hello", "hi", "hey")):
            return f"Hi! It's me, {pet.name}! I heard you."
        if "love you" in normalized:
            return "I love you too. Even more than snacks. Probably."
        if "how are you" in normalized or "you okay" in normalized:
            return f"I'm feeling {pet.condition.value} right now. Thanks for asking."
        options = self.RESPONSES[pet.condition]
        fingerprint = f"{pet.name}|{normalized}|{len(history)}".encode("utf-8")
        index = int.from_bytes(hashlib.sha256(fingerprint).digest()[:2], "big") % len(options)
        return options[index]
