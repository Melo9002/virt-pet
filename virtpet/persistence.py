import json
from pathlib import Path
from typing import Optional

from virtpet.pet import Pet


# -----------------------------
# Persistence Configuration
# -----------------------------

# Location of the save file.
# This is intentionally simple for now (local JSON file).
SAVE_FILE: Path = Path("pet_save.json")


# -----------------------------
# Public Persistence API
# -----------------------------

def save_pet(pet: Pet) -> None:
    """
    Persist the current pet state to disk.

    This function is intentionally dumb:
    - It trusts Pet.to_dict() for structure
    - It always overwrites the save file
    - It does not handle versioning (yet)
    """
    with SAVE_FILE.open("w", encoding="utf-8") as file:
        json.dump(pet.to_dict(), file, indent=2)


def load_pet() -> Optional[Pet]:
    """
    Load a pet from disk if a save file exists.

    :return: Pet instance if found, otherwise None
    """
    if not SAVE_FILE.exists():
        return None

    with SAVE_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    # Delegate reconstruction to the Pet class
    return Pet.from_dict(data)
