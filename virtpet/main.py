import argparse

from virtpet.engine import GameEngine
from virtpet.persistence import load_pet
from virtpet.pet import Pet
from virtpet.ui_curses import CursesUI


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
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    speed = 60.0 if args.debug else 1.0
    engine = GameEngine(create_pet(), minutes_per_real_second=speed)
    try:
        CursesUI(engine).run()
    finally:
        engine.stop()


if __name__ == "__main__":
    main()
