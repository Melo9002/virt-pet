import unittest

from virtpet.pet import Pet, PetCondition, PetState


class PetTests(unittest.TestCase):
    def test_tick_advances_needs_at_intervals(self):
        pet = Pet("Pip")
        pet.tick(60)
        self.assertEqual((pet.age, pet.hunger, pet.happiness), (60, 37, 69))

    def test_sleep_slows_hunger_and_protects_happiness(self):
        pet = Pet("Pip", state=PetState.SLEEPING)
        pet.tick(60)
        self.assertEqual((pet.age, pet.hunger, pet.happiness), (60, 36, 70))

    def test_pause_freezes_time_and_blocks_actions(self):
        pet = Pet("Pip", paused=True)
        pet.tick(120)
        self.assertEqual(pet.age, 0)
        self.assertFalse(pet.feed())

    def test_round_trip_preserves_internal_timers(self):
        pet = Pet("Pip")
        pet.tick(29)
        restored = Pet.from_dict(pet.to_dict())
        restored.tick(1)
        self.assertEqual(restored.hunger, 36)

    def test_legacy_save_is_supported_and_clamped(self):
        pet = Pet.from_dict({"name": "Pip", "age": 2, "hunger": 150,
                             "happiness": -2, "state": "unknown"})
        self.assertEqual((pet.hunger, pet.happiness), (100, 0))
        self.assertEqual(pet.state, PetState.IDLE)

    def test_conditions_are_prioritized(self):
        self.assertEqual(Pet("Pip", hunger=70).condition, PetCondition.HUNGRY)
        self.assertEqual(Pet("Pip", toilet=65).condition, PetCondition.DIRTY)
        self.assertEqual(Pet("Pip", happiness=35).condition, PetCondition.LONELY)
        self.assertEqual(Pet("Pip", tiredness=70).condition, PetCondition.SLEEPY)
        sick = Pet("Pip", hunger=95, toilet=95)
        self.assertEqual(sick.condition, PetCondition.SICK)

    def test_sleep_restores_tiredness(self):
        pet = Pet("Pip", state=PetState.SLEEPING, tiredness=20)
        pet.tick(10)
        self.assertEqual(pet.tiredness, 18)


if __name__ == "__main__":
    unittest.main()
