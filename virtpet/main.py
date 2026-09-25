import argparse
import getpass
import os

from virtpet.engine import GameEngine
from virtpet.persistence import load_pet
from virtpet.pet import Pet
from virtpet.settings import VoiceSettings, setup_voice
from virtpet.ui_curses import CursesUI
from virtpet.voice import (FallbackVoice, LocalLlamaVoice, OpenAIVoice,
                           ResilientVoice, application_dir)


def create_pet() -> Pet:
    pet = load_pet()
    if pet is not None:
        return pet
    try:
        name = input("A new egg appears! What will you name it? ").strip()
    except (EOFError, KeyboardInterrupt):
        name = ""
    return Pet(name or "Basilisk-chan")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="A cozy virtual pet for your terminal")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="run at 60 in-game minutes per real second for balancing",
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="choose the conversation provider again",
    )
    return parser.parse_args(argv)


def build_voice(settings: VoiceSettings):
    if settings.provider == "local":
        root = application_dir()
        voice = LocalLlamaVoice(root / settings.local_server, root / settings.local_model)
        return ResilientVoice(voice), "local AI"
    if settings.provider == "openai":
        api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not api_key:
            try:
                api_key = getpass.getpass(
                    "OpenAI API key (used for this run only; input is hidden): "
                ).strip()
            except (EOFError, KeyboardInterrupt):
                api_key = ""
        if api_key:
            return ResilientVoice(OpenAIVoice(api_key, settings.model)), "OpenAI"
        print("No key supplied; using the Classic voice.")
    return FallbackVoice(), "classic"


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    speed = 60.0 if args.debug else 1.0
    voice, voice_name = build_voice(setup_voice(force=args.setup))
    engine = GameEngine(create_pet(), minutes_per_real_second=speed, voice=voice)
    engine.voice_name = voice_name
    try:
        CursesUI(engine).run()
    finally:
        engine.stop()


if __name__ == "__main__":
    main()
