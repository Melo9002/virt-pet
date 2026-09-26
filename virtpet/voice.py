from __future__ import annotations

import hashlib
import json
import os
import re
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Sequence

from virtpet.pet import Pet, PetCondition, PetState


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


def _windows_llama_pids() -> set[int]:
    """Return llama-server PIDs through the native Windows process snapshot API."""
    import ctypes
    from ctypes import wintypes

    class ProcessEntry(ctypes.Structure):
        _fields_ = [
            ("dwSize", wintypes.DWORD),
            ("cntUsage", wintypes.DWORD),
            ("th32ProcessID", wintypes.DWORD),
            ("th32DefaultHeapID", ctypes.c_size_t),
            ("th32ModuleID", wintypes.DWORD),
            ("cntThreads", wintypes.DWORD),
            ("th32ParentProcessID", wintypes.DWORD),
            ("pcPriClassBase", wintypes.LONG),
            ("dwFlags", wintypes.DWORD),
            ("szExeFile", wintypes.WCHAR * 260),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    snapshot_processes = kernel32.CreateToolhelp32Snapshot
    snapshot_processes.argtypes = [wintypes.DWORD, wintypes.DWORD]
    snapshot_processes.restype = wintypes.HANDLE
    process_first = kernel32.Process32FirstW
    process_first.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry)]
    process_first.restype = wintypes.BOOL
    process_next = kernel32.Process32NextW
    process_next.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry)]
    process_next.restype = wintypes.BOOL

    snapshot = snapshot_processes(0x00000002, 0)
    if snapshot == wintypes.HANDLE(-1).value:
        return set()
    pids = set()
    entry = ProcessEntry()
    entry.dwSize = ctypes.sizeof(ProcessEntry)
    try:
        if process_first(snapshot, ctypes.byref(entry)):
            while True:
                if entry.szExeFile.lower() == "llama-server.exe":
                    pids.add(entry.th32ProcessID)
                if not process_next(snapshot, ctypes.byref(entry)):
                    break
        return pids
    finally:
        kernel32.CloseHandle(snapshot)


def _instructions(pet: Pet) -> str:
    activity = "asleep" if pet.state == PetState.SLEEPING else "awake"
    acting_cue = {
        PetCondition.CONTENT: "Sound cheerful, cozy, and curious.",
        PetCondition.HUNGRY: (
            "Your tummy is rumbling and you really want a snack. Mention hunger "
            "or food naturally in your reply."
        ),
        PetCondition.LONELY: "Sound tender and especially glad the human is here.",
        PetCondition.DIRTY: (
            "Your room needs tidying. Sound sheepish about the mess, not your body."
        ),
        PetCondition.SLEEPY: "Sound drowsy, with a soft half-asleep reply.",
        PetCondition.SICK: "Sound quiet and wobbly, and ask for gentle care if relevant.",
    }[pet.condition]
    sleep_cue = (
        "You are asleep. Answer as if mumbling from a dream; do not wake up. "
        if pet.state == PetState.SLEEPING else
        "You are awake. "
    )
    return (
        f"You are {pet.name}, a tiny creature in a cozy terminal home. The user "
        f"is your favorite visitor, not {pet.name}. In the user's message, 'you' "
        f"means you, {pet.name}; answer about yourself with 'I', 'me', or 'my'. "
        f"If the user says '{pet.name}' or 'little {pet.name}', they mean you; "
        f"never address the user as {pet.name}. Example: user says 'little "
        f"{pet.name}?' and you answer 'Mmm, that's me.' "
        "Be affectionate, impish, and occasionally dramatic. Answer the newest "
        "message directly in one natural "
        "sentence of at most 15 words. Stay inside your tiny world. Never say AI, "
        "virtual pet, human player, prompt, instructions, model, or statistics. "
        "Do not invent actions or changes. "
        f"Needs: hunger {pet.hunger}/100, happiness {pet.happiness}/100, "
        f"mess {pet.toilet}/100, tiredness {pet.tiredness}/100. "
        f"Scene: {activity}; mood: {pet.condition.value}. {sleep_cue}{acting_cue} "
        "Make this scene and mood clear in your reply when relevant."
    )


def _provider_messages(
    pet: Pet, history: Sequence[ChatMessage], message: str,
    *, reinforce_scene: bool = False,
) -> list[dict[str, str]]:
    messages = []
    for item in history[-6:]:
        role = "assistant" if item.speaker == pet.name else "user"
        messages.append({"role": role, "content": item.text})
    if reinforce_scene:
        if pet.state == PetState.SLEEPING:
            reminder = "You are asleep. Reply drowsily without waking up."
        else:
            reminder = {
                PetCondition.CONTENT: "You are awake and content.",
                PetCondition.HUNGRY: (
                    "Your tummy is rumbling and you want a snack. Mention hunger "
                    "or food naturally in this reply."
                ),
                PetCondition.LONELY: "You are awake and lonely; sound glad for company.",
                PetCondition.DIRTY: (
                    "Your room is messy and needs tidying. React sheepishly to the mess."
                ),
                PetCondition.SLEEPY: "You are awake but sleepy; sound drowsy.",
                PetCondition.SICK: "You are awake but sick; sound quiet and wobbly.",
            }[pet.condition]
        message = f"[{reminder}] Visitor says: {message}"
    messages.append({"role": "user", "content": message})
    return messages


def _local_messages(
    pet: Pet, history: Sequence[ChatMessage], message: str
) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": _instructions(pet)},
        *_provider_messages(pet, history, message, reinforce_scene=True),
    ]


def _bounded_reply(text: str, max_words: int = 15) -> str:
    """Enforce the tiny one-sentence reply promised by every AI voice."""
    normalized = " ".join(text.strip().split())
    if not normalized:
        raise RuntimeError("The provider returned no text")
    first_sentence = re.match(r"^.*?[.!?](?:\s|$)", normalized)
    if first_sentence:
        normalized = first_sentence.group(0).strip()
    words = normalized.split()
    if len(words) > max_words:
        return " ".join(words[:max_words]).rstrip(",;:") + "..."
    if normalized[-1] not in ".!?":
        normalized += "."
    return normalized


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
            "input": _provider_messages(pet, history, message),
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
                    return _bounded_reply(content["text"])
        raise RuntimeError("The API returned no text")


class LocalLlamaVoice:
    """Run a bundled llama.cpp server and use its OpenAI-compatible endpoint."""

    def __init__(self, server_path: Path, model_path: Path, port: int = 8132):
        self.server_path = server_path
        self.model_path = model_path
        self.port = port
        self._process: subprocess.Popen | None = None
        self._initial_process_ids: set[int] = set()

    def _ensure_server(self) -> None:
        if self._process is not None and self._process.poll() is None:
            return
        if not self.server_path.exists() or not self.model_path.exists():
            raise FileNotFoundError("Local model runtime is not installed")
        try:
            with socket.create_connection(("127.0.0.1", self.port), timeout=0.2):
                raise RuntimeError(f"Local model port {self.port} is already in use")
        except OSError:
            pass
        flags = 0
        start_new_session = False
        if sys.platform == "win32":
            flags = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
            self._initial_process_ids = _windows_llama_pids()
        else:
            start_new_session = True
        self._process = subprocess.Popen(
            [str(self.server_path), "-m", str(self.model_path), "--host", "127.0.0.1",
             "--port", str(self.port), "-c", "1024", "-ngl", "0"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=flags,
            start_new_session=start_new_session,
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
            "messages": _local_messages(pet, history, message),
            "max_tokens": 40,
            "temperature": 0.8,
        }).encode("utf-8")
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/v1/chat/completions",
            data=payload, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))
        return _bounded_reply(data["choices"][0]["message"]["content"])

    def close(self) -> None:
        if self._process is not None and self._process.poll() is None:
            if sys.platform == "win32":
                subprocess.run(
                    ["taskkill", "/PID", str(self._process.pid), "/T", "/F"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
                stopped_processes = {self._process.pid}
                for _ in range(20):
                    time.sleep(0.1)
                    spawned_processes = (
                        _windows_llama_pids()
                        - self._initial_process_ids
                        - stopped_processes
                    )
                    for process_id in spawned_processes:
                        subprocess.run(
                            ["taskkill", "/PID", str(process_id), "/T", "/F"],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            check=False,
                        )
                    stopped_processes.update(spawned_processes)
            else:
                os.killpg(self._process.pid, signal.SIGTERM)
                try:
                    self._process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    os.killpg(self._process.pid, signal.SIGKILL)
                    self._process.wait(timeout=3)
            self._process = None
            self._initial_process_ids.clear()


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
