"""Exercise the prepared llama.cpp runtime through the real voice adapter."""

from pathlib import Path
from time import monotonic

from virtpet.pet import Pet
from virtpet.settings import VoiceSettings
from virtpet.voice import LocalLlamaVoice


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    settings = VoiceSettings(provider="local")
    voice = LocalLlamaVoice(
        root / settings.local_server,
        root / settings.local_model,
        port=18132,
    )
    started = monotonic()
    try:
        reply = voice.reply(Pet("Release Chick"), "Can you hear me?")
    finally:
        voice.close()
    print(f"Local AI reply ({monotonic() - started:.2f}s): {reply}")


if __name__ == "__main__":
    main()
