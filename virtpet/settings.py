from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


SETTINGS_FILE = Path("settings.json")
PROVIDERS = {"classic", "local", "openai"}


@dataclass
class VoiceSettings:
    provider: str = "classic"
    model: str = "gpt-5.4-nano"
    local_model: str = "models/smollm2-360m-instruct-q8_0.gguf"
    local_server: str = "runtime/llama-server.exe"


def load_settings() -> VoiceSettings | None:
    if not SETTINGS_FILE.exists():
        return None
    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        settings = VoiceSettings(**{
            key: value for key, value in data.items()
            if key in VoiceSettings.__dataclass_fields__
        })
        if settings.provider not in PROVIDERS:
            return None
        return settings
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return None


def save_settings(settings: VoiceSettings) -> None:
    """Save preferences only. API keys deliberately never enter this file."""
    temporary = SETTINGS_FILE.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(asdict(settings), indent=2), encoding="utf-8")
    temporary.replace(SETTINGS_FILE)


def setup_voice(force: bool = False) -> VoiceSettings:
    existing = load_settings()
    if existing is not None and not force:
        return existing

    print("\nHow should your pet speak?")
    print("  [1] Classic voice  - cute, deterministic, no AI")
    print("  [2] Local tiny LLM - private and offline (requires bundled model)")
    print("  [3] OpenAI API     - requires OPENAI_API_KEY")
    try:
        choice = input("Choose 1, 2, or 3 [1]: ").strip() or "1"
    except (EOFError, KeyboardInterrupt):
        choice = "1"

    provider = {"1": "classic", "2": "local", "3": "openai"}.get(choice, "classic")
    settings = VoiceSettings(provider=provider)
    if provider == "openai":
        try:
            model = input(f"Model [{settings.model}]: ").strip()
            if model:
                settings.model = model
        except (EOFError, KeyboardInterrupt):
            pass
    save_settings(settings)
    return settings
