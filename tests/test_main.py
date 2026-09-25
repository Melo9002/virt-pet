import unittest

from virtpet.main import parse_args


class CommandLineTests(unittest.TestCase):
    def test_voice_test_flag(self):
        arguments = parse_args(["--voice-test"])
        self.assertTrue(arguments.voice_test)
        self.assertFalse(arguments.debug)
        self.assertFalse(arguments.setup)


if __name__ == "__main__":
    unittest.main()
