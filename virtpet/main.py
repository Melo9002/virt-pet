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


def main() -> None:
    engine = GameEngine(create_pet(), minutes_per_real_second=1.0)
    try:
        CursesUI(engine).run()
    finally:
        engine.stop()


if __name__ == "__main__":
    main()
