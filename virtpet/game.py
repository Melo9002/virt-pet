import json
from pathlib import Path
from virtpet.pet import Pet


def show_status(pet: Pet):
    """
    Renders the pet's current state to the player.
    This is presentation logic, not game logic.
    """
    print("\n--- STATUS ---")
    print(f"Name: {pet.name}")
    print(f"Age: {pet.age}")
    print(f"Hunger: {pet.hunger}")
    print(f"Energy: {pet.energy}")
    print(f"Happiness: {pet.happiness}")

SAVE_FILE = Path("pet_save.json")


def load_pet() -> Pet:
    """
    Load pet from disk if it exists, otherwise create a new one.
    """
    if SAVE_FILE.exists():
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        print("A familiar presence awakens...")
        return Pet.from_dict(data)

    print("A new egg appears...")
    return Pet("Basilisk-chan")


def save_pet(pet: Pet):
    """
    Persist the pet's current state to disk.
    """
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(pet.to_dict(), f, indent=2)


def run():
    """
    Main game loop.
    Owns the pet instance and controls time progression.
    """
    pet = load_pet()

    while True:
        show_status(pet)

        # Player input is normalized immediately
        action = input("\nAction (feed/play/sleep/quit): ").strip().lower()

        # Dispatch player intent to pet behavior
        if action == "feed":
            pet.feed()
        elif action == "play":
            pet.play()
        elif action == "sleep":
            pet.sleep()
        elif action == "quit":
            print("You walk away. Time continues.")
            break
        else:
            # Invalid input still consumes time
            print("It doesn’t understand.")

        # Time always moves forward
        pet.tick()
        save_pet(pet)
