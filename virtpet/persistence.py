import json
import os
from pathlib import Path
from typing import Optional

from virtpet.pet import Pet

SAVE_FILE = Path(os.environ.get("VIRTPET_SAVE_FILE", "pet_save.json"))


def save_pet(pet: Pet) -> None:
    """Write atomically so an interrupted save cannot ruin the pet."""
    temporary = SAVE_FILE.with_suffix(SAVE_FILE.suffix + ".tmp")
    SAVE_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary.write_text(json.dumps(pet.to_dict(), indent=2), encoding="utf-8")
    temporary.replace(SAVE_FILE)


def load_pet() -> Optional[Pet]:
    if not SAVE_FILE.exists():
        return None
    try:
        return Pet.from_dict(json.loads(SAVE_FILE.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, TypeError, ValueError, KeyError):
        try:
            SAVE_FILE.replace(SAVE_FILE.with_suffix(SAVE_FILE.suffix + ".corrupt"))
        except OSError:
            pass
        return None
