import unittest

from virtpet.pet import Pet
from virtpet.voice import ChatMessage, FallbackVoice


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


if __name__ == "__main__":
    unittest.main()
