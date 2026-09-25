import unittest

from virtpet.pet import Pet
from virtpet.voice import ChatMessage, FallbackVoice, ResilientVoice


class FallbackVoiceTests(unittest.TestCase):
    def test_same_context_has_same_reply(self):
        voice = FallbackVoice()
        pet = Pet("Pip")
        history = (ChatMessage("you", "Earlier"),)
        first = voice.reply(pet, "Tell me something", history)
        second = voice.reply(pet, "Tell me something", history)
        self.assertEqual(first, second)

    def test_reply_reflects_condition(self):
        reply = FallbackVoice().reply(Pet("Pip", hunger=80), "How are you?")
        self.assertIn("hungry", reply)

    def test_provider_failure_falls_back(self):
        class BrokenVoice:
            def reply(self, pet, message, history=()):
                raise RuntimeError("nope")

        voice = ResilientVoice(BrokenVoice())
        reply = voice.reply(Pet("Pip"), "hello")
        self.assertIn("Pip", reply)
        self.assertEqual(voice.last_error, "nope")


if __name__ == "__main__":
    unittest.main()
