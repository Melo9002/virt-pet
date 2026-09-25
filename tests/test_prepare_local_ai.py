import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "prepare_local_ai.py"
SPEC = importlib.util.spec_from_file_location("prepare_local_ai", SCRIPT)
prepare_local_ai = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(prepare_local_ai)


class LocalAIPreparationTests(unittest.TestCase):
    def test_windows_selects_the_cpu_zip(self):
        with (
            patch.object(prepare_local_ai.sys, "platform", "win32"),
            patch.object(prepare_local_ai.platform, "machine", return_value="AMD64"),
        ):
            pattern, server = prepare_local_ai._asset_pattern()
        self.assertTrue(pattern.search("llama-b123-bin-win-cpu-x64.zip"))
        self.assertEqual(server, "llama-server.exe")

    def test_linux_selects_the_ubuntu_archive(self):
        with (
            patch.object(prepare_local_ai.sys, "platform", "linux"),
            patch.object(prepare_local_ai.platform, "machine", return_value="x86_64"),
        ):
            pattern, server = prepare_local_ai._asset_pattern()
        self.assertTrue(pattern.search("llama-b123-bin-ubuntu-x64.tar.gz"))
        self.assertEqual(server, "llama-server")

    def test_stable_release_can_follow_its_nightly_build(self):
        stable = {
            "assets": [],
            "body": "Nightly: https://github.com/ggml-org/llama.cpp/releases/tag/b123",
        }
        nightly = {"assets": [{
            "name": "llama-b123-bin-win-cpu-x64.zip",
            "browser_download_url": "https://example.invalid/llama.zip",
        }]}
        with (
            patch.object(prepare_local_ai.sys, "platform", "win32"),
            patch.object(prepare_local_ai.platform, "machine", return_value="AMD64"),
            patch.object(prepare_local_ai, "_read_json", side_effect=[stable, nightly]),
        ):
            asset, server = prepare_local_ai._runtime_asset()
        self.assertEqual(asset, nightly["assets"][0])
        self.assertEqual(server, "llama-server.exe")


if __name__ == "__main__":
    unittest.main()
