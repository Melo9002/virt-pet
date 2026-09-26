import unittest

from virtpet.engine import GameEngine
from virtpet.pet import Pet


class FakeClock:
    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


class GameEngineTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.saved = []
        self.pet = Pet("Pip")
        self.engine = GameEngine(
            self.pet,
            clock=self.clock,
            saver=lambda pet: self.saved.append(pet.to_dict()),
        )

    def test_elapsed_time_advances_pet_and_saves(self):
        self.clock.advance(30)
        self.engine.update()
        self.assertEqual(self.pet.age, 30)
        self.assertEqual(len(self.saved), 1)

    def test_debug_speed_accelerates_time(self):
        engine = GameEngine(self.pet, minutes_per_real_second=60,
                            clock=self.clock, saver=lambda pet: None)
        self.clock.advance(2)
        engine.update()
        self.assertEqual(self.pet.age, 120)

    def test_pause_does_not_accumulate_elapsed_time(self):
        self.engine.toggle_pause()
        self.clock.advance(100)
        self.engine.update()
        self.engine.toggle_pause()
        self.clock.advance(1)
        self.engine.update()
        self.assertEqual(self.pet.age, 1)

    def test_actions_save_immediately(self):
        self.assertTrue(self.engine.feed())
        self.assertEqual(len(self.saved), 1)

    def test_blocked_action_reports_failure(self):
        self.pet.paused = True

        self.assertFalse(self.engine.play())

    def test_chat_is_trimmed_and_keeps_roles(self):
        self.engine.talk("   hello    there   ")
        messages = list(self.engine.conversation)
        self.assertEqual(messages[0].text, "hello there")
        self.assertEqual(messages[0].speaker, "you")
        self.assertEqual(messages[1].speaker, "Pip")

    def test_voice_status_reveals_a_classic_fallback(self):
        self.engine.voice_name = "local AI"
        self.engine.voice.last_error = "Local model port is already in use"

        self.assertEqual(
            self.engine.voice_status,
            "local AI -> classic fallback",
        )


if __name__ == "__main__":
    unittest.main()
