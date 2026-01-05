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


def run():
    """
    Main game loop.
    Owns the pet instance and controls time progression.
    """
    pet = Pet("Basilisk-chan")

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
