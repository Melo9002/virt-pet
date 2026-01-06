import json
from pathlib import Path
from virtpet.pet import Pet

SAVE_FILE = Path("pet_save.json")


def save_pet(pet: Pet) -> None:
    """
    Persist the pet state to disk.
    """
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(pet.to_dict(), f, indent=2)


def load_pet() -> Pet | None:
    """
    Load pet from disk if it exists.
    Returns None if no save is found.
    """
    if not SAVE_FILE.exists():
        return None

    with open(SAVE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    return Pet.from_dict(data)
