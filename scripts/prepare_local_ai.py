"""Download the platform llama.cpp runtime, SmolLM2 model, and licenses."""

from __future__ import annotations

import json
import platform
import re
import shutil
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
RUNTIME_DIR = PROJECT_ROOT / "runtime"
MODELS_DIR = PROJECT_ROOT / "models"
LICENSES_DIR = PROJECT_ROOT / "THIRD_PARTY_LICENSES"
GITHUB_RELEASES = "https://api.github.com/repos/ggml-org/llama.cpp/releases"
MODEL_NAME = "smollm2-360m-instruct-q8_0.gguf"
MODEL_URL = (
    "https://huggingface.co/HuggingFaceTB/SmolLM2-360M-Instruct-GGUF/"
    f"resolve/main/{MODEL_NAME}?download=true"
)


def _request(url: str) -> urllib.request.Request:
    return urllib.request.Request(url, headers={"User-Agent": "virt-pet-builder"})


def _read_json(url: str) -> dict:
    with urllib.request.urlopen(_request(url), timeout=30) as response:
        return json.load(response)


def _asset_pattern() -> tuple[re.Pattern[str], str]:
    machine = platform.machine().lower()
    if machine not in {"amd64", "x86_64"}:
        raise RuntimeError(f"Unsupported CPU architecture: {machine}")
    if sys.platform == "win32":
        return re.compile(r"bin-win-cpu-x64\.zip$"), "llama-server.exe"
    if sys.platform.startswith("linux"):
        return re.compile(r"bin-ubuntu-x64\.tar\.gz$"), "llama-server"
    raise RuntimeError(f"Local AI preparation is not supported on {sys.platform}")


def _find_asset(release: dict, pattern: re.Pattern[str]) -> dict | None:
    return next(
        (asset for asset in release.get("assets", ()) if pattern.search(asset["name"])),
        None,
    )


def _runtime_asset() -> tuple[dict, str]:
    pattern, server_name = _asset_pattern()
    release = _read_json(f"{GITHUB_RELEASES}/latest")
    asset = _find_asset(release, pattern)
    if asset is None:
        nightly = re.search(r"releases/tag/(b\d+)", release.get("body", ""))
        if nightly:
            release = _read_json(f"{GITHUB_RELEASES}/tags/{nightly.group(1)}")
            asset = _find_asset(release, pattern)
    if asset is None:
        raise RuntimeError("No compatible llama.cpp CPU release was found")
    return asset, server_name


def _download(url: str, destination: Path) -> None:
    with urllib.request.urlopen(_request(url), timeout=60) as response:
        with destination.open("wb") as output:
            shutil.copyfileobj(response, output)


def _extract(archive: Path, destination: Path) -> None:
    if archive.name.endswith(".zip"):
        with zipfile.ZipFile(archive) as package:
            package.extractall(destination)
    else:
        with tarfile.open(archive, "r:gz") as package:
            try:
                package.extractall(destination, filter="data")
            except TypeError:  # Python 3.10 and 3.11 lack extraction filters.
                package.extractall(destination)


def _copy_runtime(extracted: Path, server_name: str) -> None:
    server = next(extracted.rglob(server_name), None)
    if server is None:
        raise RuntimeError(f"{server_name} was not present in the llama.cpp release")
    shutil.copytree(server.parent, RUNTIME_DIR, dirs_exist_ok=True)


def main() -> None:
    for directory in (RUNTIME_DIR, MODELS_DIR, LICENSES_DIR):
        directory.mkdir(parents=True, exist_ok=True)

    print("Finding the latest llama.cpp CPU build...")
    asset, server_name = _runtime_asset()
    with tempfile.TemporaryDirectory(prefix="virt-pet-") as temporary:
        temporary_dir = Path(temporary)
        archive = temporary_dir / asset["name"]
        extracted = temporary_dir / "llama"
        extracted.mkdir()
        _download(asset["browser_download_url"], archive)
        _extract(archive, extracted)
        _copy_runtime(extracted, server_name)

    model_path = MODELS_DIR / MODEL_NAME
    if not model_path.exists():
        print("Downloading SmolLM2-360M-Instruct (386 MB)...")
        _download(MODEL_URL, model_path)

    _download(
        "https://raw.githubusercontent.com/ggml-org/llama.cpp/master/LICENSE",
        LICENSES_DIR / "llama.cpp-MIT.txt",
    )
    _download(
        "https://www.apache.org/licenses/LICENSE-2.0.txt",
        LICENSES_DIR / "SmolLM2-Apache-2.0.txt",
    )
    print("Local AI is ready. Run: python -m virtpet.main --setup")


if __name__ == "__main__":
    main()
