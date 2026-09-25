from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
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


def _instructions(pet: Pet) -> str:
    return (
        f"You are {pet.name}, a tiny virtual pet. Reply in one cute sentence of "
        "at most 15 words. Be warm, playful, and slightly silly. Never act like "
        "an assistant. Do not claim the pet's condition changed. "
        f"Current condition: {pet.condition.value}. Hunger: {pet.hunger}/100. "
        f"Happiness: {pet.happiness}/100. Mess: {pet.toilet}/100. "
        f"Tiredness: {pet.tiredness}/100."
    )


def _history_text(history: Sequence[ChatMessage], message: str) -> str:
    recent = "\n".join(f"{item.speaker}: {item.text}" for item in history[-6:])
    return f"{recent}\nuser: {message}" if recent else message


class OpenAIVoice:
    """Small standard-library adapter for OpenAI's Responses API."""

    def __init__(self, api_key: str, model: str = "gpt-5.4-nano",
                 timeout: float = 30.0):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def reply(self, pet: Pet, message: str,
              history: Sequence[ChatMessage] = ()) -> str:
        payload = json.dumps({
            "model": self.model,
            "instructions": _instructions(pet),
            "input": _history_text(history, message),
            "max_output_tokens": 40,
            "store": False,
        }).encode("utf-8")
        request = urllib.request.Request(
            "https://api.openai.com/v1/responses",
            data=payload,
            headers={"Authorization": f"Bearer {self.api_key}",
                     "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        for output in data.get("output", []):
            for content in output.get("content", []):
                if content.get("type") == "output_text" and content.get("text"):
                    return content["text"].strip()
        raise RuntimeError("The API returned no text")


class LocalLlamaVoice:
    """Run a bundled llama.cpp server and use its OpenAI-compatible endpoint."""

    def __init__(self, server_path: Path, model_path: Path, port: int = 8132):
        self.server_path = server_path
        self.model_path = model_path
        self.port = port
        self._process: subprocess.Popen | None = None

    def _ensure_server(self) -> None:
        if self._process is not None and self._process.poll() is None:
            return
        if not self.server_path.exists() or not self.model_path.exists():
            raise FileNotFoundError("Local model runtime is not installed")
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        self._process = subprocess.Popen(
            [str(self.server_path), "-m", str(self.model_path), "--host", "127.0.0.1",
             "--port", str(self.port), "-c", "1024", "-ngl", "0"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=flags,
        )
        health = f"http://127.0.0.1:{self.port}/health"
        for _ in range(100):
            if self._process.poll() is not None:
                break
            try:
                with urllib.request.urlopen(health, timeout=0.25):
                    return
            except (OSError, urllib.error.URLError):
                time.sleep(0.1)
        self.close()
        raise RuntimeError("Local model did not start")

    def reply(self, pet: Pet, message: str,
              history: Sequence[ChatMessage] = ()) -> str:
        self._ensure_server()
        payload = json.dumps({
            "messages": [
                {"role": "system", "content": _instructions(pet)},
                {"role": "user", "content": _history_text(history, message)},
            ],
            "max_tokens": 40,
            "temperature": 0.8,
        }).encode("utf-8")
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/v1/chat/completions",
            data=payload, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()

    def close(self) -> None:
        if self._process is not None and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._process.kill()


class ResilientVoice:
    """Keep the pet responsive when an optional AI provider fails."""

    def __init__(self, primary: PetVoice, fallback: PetVoice | None = None):
        self.primary = primary
        self.fallback = fallback or FallbackVoice()
        self.last_error: str | None = None

    def reply(self, pet: Pet, message: str,
              history: Sequence[ChatMessage] = ()) -> str:
        try:
            self.last_error = None
            return self.primary.reply(pet, message, history)
        except Exception as error:
            self.last_error = str(error)
            return self.fallback.reply(pet, message, history)

    def close(self) -> None:
        close = getattr(self.primary, "close", None)
        if close is not None:
            close()


def application_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


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
