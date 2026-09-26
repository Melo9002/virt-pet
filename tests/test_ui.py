import unittest

from virtpet.pet import PetCondition, PetState
from virtpet.sprites import pet_art
from virtpet.ui_curses import _conversation_lines
from virtpet.voice import ChatMessage


class ConversationLayoutTests(unittest.TestCase):
    def test_long_latest_reply_wraps_without_losing_text(self):
        messages = (
            ChatMessage("you", "Oh my god you're so cute!!"),
            ChatMessage(
                "Little Guy",
                "I'm just trying to be as happy and full of energy as possible!",
            ),
        )

        lines = _conversation_lines(messages)

        self.assertLessEqual(len(lines), 3)
        rendered = " ".join(line.strip() for line in lines)
        self.assertIn("energy as possible!", rendered)
        self.assertTrue(all(len(line) <= 56 for line in lines))


class PetSpriteTests(unittest.TestCase):
    def test_every_condition_has_a_compact_five_line_sprite(self):
        for condition in PetCondition:
            with self.subTest(condition=condition):
                art = pet_art(condition, PetState.IDLE, frame=0)
                self.assertEqual(len(art), 5)
                self.assertTrue(all(len(line) <= 10 for line in art))

    def test_content_pet_blinks_and_moves_its_tail(self):
        awake = pet_art(PetCondition.CONTENT, PetState.IDLE, frame=0)
        animated = pet_art(PetCondition.CONTENT, PetState.IDLE, frame=15)

        self.assertIn("^.^", "\n".join(awake))
        self.assertIn("-.-", "\n".join(animated))
        self.assertNotEqual(awake, animated)

    def test_paused_sprite_is_stable(self):
        first = pet_art(PetCondition.CONTENT, PetState.IDLE, frame=0, paused=True)
        later = pet_art(PetCondition.CONTENT, PetState.IDLE, frame=999, paused=True)

        self.assertEqual(first, later)

    def test_sleeping_sprite_has_dream_particles(self):
        art = pet_art(PetCondition.SLEEPY, PetState.SLEEPING, frame=5)

        self.assertIn("z Z", "\n".join(art))


if __name__ == "__main__":
    unittest.main()
