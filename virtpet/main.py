from virtpet.pet import Pet
from virtpet.engine import GameEngine
from virtpet.ui_curses import CursesUI
from virtpet.persistence import load_pet

if __name__ == "__main__":
    pet = load_pet()

    if pet is None:
        name = input("Give your pet a name: ").strip()
        if not name:
            name = "Basilisk-chan"
        pet = Pet(name)

    # 1 real second = 1 in-game minute
    engine = GameEngine(pet, minutes_per_real_second=1.0)

    ui = CursesUI(engine)

    # Run engine in background-like loop
    import threading
    engine_thread = threading.Thread(target=engine.run, daemon=True)
    engine_thread.start()

    ui.run()
