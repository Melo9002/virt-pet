import unittest

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


if __name__ == "__main__":
    unittest.main()
