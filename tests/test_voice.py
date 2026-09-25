import json
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from virtpet.pet import Pet
from virtpet.voice import (
    ChatMessage,
    FallbackVoice,
    LocalLlamaVoice,
    OpenAIVoice,
    ResilientVoice,
    _bounded_reply,
    _local_messages,
)


class FallbackVoiceTests(unittest.TestCase):
    def test_local_voice_closes_the_windows_process_tree(self):
        class FakeProcess:
            pid = 123

            def poll(self):
                return None

        voice = LocalLlamaVoice(Path("server"), Path("model"))
        voice._process = FakeProcess()
        voice._initial_process_ids = {50}
        with (
            patch("virtpet.voice.sys.platform", "win32"),
            patch("virtpet.voice._windows_llama_pids", return_value={50, 124}),
            patch("virtpet.voice.time.sleep"),
            patch("virtpet.voice.subprocess.run") as run,
        ):
            voice.close()
        self.assertEqual(
            [call.args[0] for call in run.call_args_list],
            [
                ["taskkill", "/PID", "123", "/T", "/F"],
                ["taskkill", "/PID", "124", "/T", "/F"],
            ],
        )
        self.assertIsNone(voice._process)

    def test_openai_request_uses_key_roles_and_parses_reply(self):
        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return json.dumps({
                    "output": [
                        {"type": "reasoning"},
                        {"type": "message", "content": [{
                            "type": "output_text",
                            "text": "Yes, I can hear you! I am very excited too.",
                        }]},
                    ]
                }).encode("utf-8")

        captured = {}

        def fake_urlopen(request, timeout):
            captured["request"] = request
            captured["timeout"] = timeout
            return FakeResponse()

        voice = OpenAIVoice("test-secret", model="test-model", timeout=7)
        history = (
            ChatMessage("you", "Hello!"),
            ChatMessage("Little Guy", "Hello, human friend!"),
        )
        with patch("virtpet.voice.urllib.request.urlopen", fake_urlopen):
            reply = voice.reply(Pet("Little Guy"), "Can you hear me?", history)

        request = captured["request"]
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(request.full_url, "https://api.openai.com/v1/responses")
        self.assertEqual(request.get_header("Authorization"), "Bearer test-secret")
        self.assertNotIn("test-secret", request.data.decode("utf-8"))
        self.assertEqual(captured["timeout"], 7)
        self.assertEqual(payload["model"], "test-model")
        self.assertFalse(payload["store"])
        self.assertEqual(
            [item["role"] for item in payload["input"]],
            ["user", "assistant", "user"],
        )
        self.assertEqual(reply, "Yes, I can hear you!")

    def test_local_history_uses_model_roles(self):
        pet = Pet("Little Guy")
        messages = _local_messages(
            pet,
            (
                ChatMessage("you", "Hello, little guy!"),
                ChatMessage("Little Guy", "Hello, human friend!"),
            ),
            "Can you hear me?",
        )
        self.assertEqual(
            [message["role"] for message in messages],
            ["system", "user", "assistant", "user"],
        )
        self.assertEqual(messages[-1]["content"], "Can you hear me?")

    def test_ai_reply_is_limited_to_one_short_sentence(self):
        reply = _bounded_reply(
            "I am wonderfully happy to see you today! "
            "Would you like to play a very elaborate game with me?"
        )
        self.assertEqual(reply, "I am wonderfully happy to see you today!")
        self.assertLessEqual(len(reply.split()), 15)

    def test_long_ai_sentence_is_truncated(self):
        reply = _bounded_reply(" ".join(f"word{number}" for number in range(20)))
        self.assertEqual(len(reply.split()), 15)
        self.assertTrue(reply.endswith("..."))

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
