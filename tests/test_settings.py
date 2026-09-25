import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from virtpet.settings import (
    VoiceSettings,
    default_local_server,
    load_settings,
    save_settings,
)


class SettingsTests(unittest.TestCase):
    def test_local_server_matches_the_operating_system(self):
        with patch("virtpet.settings.sys.platform", "win32"):
            self.assertEqual(default_local_server(), "runtime/llama-server.exe")
        with patch("virtpet.settings.sys.platform", "linux"):
            self.assertEqual(default_local_server(), "runtime/llama-server")

    def setUp(self):
        self.old_cwd = os.getcwd()
        self.temporary = tempfile.TemporaryDirectory()
        os.chdir(self.temporary.name)

    def tearDown(self):
        os.chdir(self.old_cwd)
        self.temporary.cleanup()

    def test_round_trip_does_not_contain_credentials(self):
        save_settings(VoiceSettings(provider="openai", model="tiny-model"))
        data = json.loads(Path("settings.json").read_text(encoding="utf-8"))
        self.assertNotIn("api_key", data)
        self.assertEqual(load_settings().model, "tiny-model")

    def test_unknown_provider_is_rejected(self):
        with open("settings.json", "w", encoding="utf-8") as file:
            json.dump({"provider": "mystery"}, file)
        self.assertIsNone(load_settings())


if __name__ == "__main__":
    unittest.main()
