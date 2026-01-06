import threading

from virtpet.pet import Pet
from virtpet.engine import GameEngine
from virtpet.ui_curses import CursesUI
from virtpet.persistence import load_pet


# -----------------------------
# Application Bootstrap
# -----------------------------

def create_pet() -> Pet:
    """
    Load an existing pet or create a new one if no save exists.
    """
    pet = load_pet()

    if pet is not None:
        return pet

    name = input("Give your pet a name: ").strip()
    if not name:
        name = "Basilisk-chan"

    return Pet(name)


def start_engine(engine: GameEngine) -> None:
    """
    Start the game engine in a background thread.
    """
    engine_thread = threading.Thread(
        target=engine.run,
        daemon=True
    )
    engine_thread.start()


def main() -> None:
    """
    Application entry point.
    Responsible only for wiring components together.
    """
    pet = create_pet()

    # 1 real second = 1 in-game minute
    engine = GameEngine(
        pet=pet,
        minutes_per_real_second=1.0
    )

    ui = CursesUI(engine)

    start_engine(engine)
    ui.run()


# -----------------------------
# Entrypoint Guard
# -----------------------------

if __name__ == "__main__":
    main()
