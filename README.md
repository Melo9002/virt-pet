# virt-pet 🐣

A tiny real-time creature that lives, grows, and chats in your terminal.

What began as a proof of concept is now a deliberately small, complete virtual-pet game: deterministic simulation underneath, optional generative personality on top, and no cloud dependency unless the player chooses one.

## Features

- Animated, responsive curses interface
- Hunger, happiness, mess, tiredness, sleep, age, and persistent internal timers
- Six derived conditions: content, hungry, lonely, dirty, sleepy, and sick
- Feed, play, sleep, wake, tidy, pause, and chat actions
- Atomic JSON saves with recovery from invalid files
- Three interchangeable conversation modes:
  - **Classic:** cute deterministic replies, offline and dependency-free
  - **Local AI:** bundled SmolLM2 through llama.cpp, private and offline
  - **OpenAI:** short generated replies through the Responses API
- Safe fallback to Classic mode if an optional provider fails
- Accelerated debug mode and automated tests

The voice can describe the pet, but it cannot change the simulation. Python remains the source of truth for every need and action.

## Run a portable edition

Download the archive for your x64 system from the latest GitHub release:

- **Windows:** extract `virt-pet-windows-x64.zip`, then run `virt-pet.exe` in a terminal.
- **Linux:** extract `virt-pet-linux-x64.tar.gz`, then run `./virt-pet` in a terminal.

Both portable editions include the local model and llama.cpp runtime, so they
do not require Python, Ollama, an account, or an internet connection. The Linux
artifact is built and smoke-tested on Ubuntu 22.04 for compatibility with a
broad range of current distributions, including Linux Mint releases based on
Ubuntu 22.04 or newer.

Keep the extracted folders beside the executable; the Local AI option needs
the bundled `models/` and `runtime/` files. The first local reply starts the
model server and may take slightly longer than later replies.

## Run from source

Requires Python 3.10 or newer.

```bash
python -m pip install -e .
virt-pet
```

On first launch, choose how the pet should speak. Run `virt-pet --setup` whenever you want to choose again. Local preferences are written to the ignored `settings.json`; secrets are never written there.

The interface needs a terminal at least 64 columns wide and 27 rows tall.

## Conversation modes

### Classic

Works immediately and always remains available as the fallback. No model, account, or network is needed.

### Local AI

Prepare the official SmolLM2 GGUF model and a CPU-only llama.cpp runtime for
your operating system.

Windows:

```powershell
./scripts/prepare_local_ai.ps1
python -m virtpet.main --setup
```

Linux:

```bash
bash ./scripts/prepare_local_ai.sh
python -m virtpet.main --setup
```

Choose option 2. Generated `models/`, `runtime/`, and third-party license directories stay outside Git but are included by the release builder. The download is approximately 386 MB plus the runtime.

If the model or runtime is missing, cannot start, or cannot generate a reply,
the pet automatically answers with its Classic voice instead. Quitting the game
also shuts down the local model server.

### OpenAI API

Set the key in the environment, then select option 3 during setup:

Windows PowerShell:

```powershell
$env:OPENAI_API_KEY = "your-key-here"
virt-pet --setup
```

Linux:

```bash
export OPENAI_API_KEY="your-key-here"
virt-pet --setup
```

If the environment variable is absent, the game requests the key with hidden input for that process only. It never stores the key in `settings.json`, the save file, or Git. The adapter uses the OpenAI Responses API and defaults to `gpt-5.4-nano`; setup allows a different model ID.

API access is entirely optional. Invalid keys, unavailable models, exhausted
quota, and network failures fall back to the Classic voice without affecting
the pet simulation.

## Controls

| Key | Action |
| ---: | :--- |
| `c` | Chat (`Enter` sends, `Esc` cancels) |
| `f` | Feed while awake |
| `p` | Play while awake |
| `s` | Sleep or wake |
| `t` | Tidy up |
| `space` | Pause or resume time |
| `q` | Save and quit |

## Debug and tests

Run one in-game hour per real second while balancing the simulation:

```bash
virt-pet --debug
```

Test the configured conversation provider without opening the interface:

```bash
virt-pet --voice-test
```

Run the test suite:

```bash
python -m unittest discover -v
```

GitHub Actions runs it on Windows and Linux with Python 3.10 and 3.13 for every push and pull request.

## Build portable releases

Windows:

```powershell
./scripts/prepare_local_ai.ps1
./scripts/build_release.ps1
```

Linux:

```bash
bash ./scripts/prepare_local_ai.sh
bash ./scripts/build_release.sh
```

These produce `dist/virt-pet-windows-x64.zip` and
`dist/virt-pet-linux-x64.tar.gz`, respectively. A tag such as `v1.0.0` runs
tests, assembles and smoke-tests both local-AI editions, and publishes both
archives to one GitHub release automatically.

## Design

- `pet.py` owns state and deterministic rules.
- `engine.py` owns elapsed time, actions, dialogue history, and lifecycle.
- `ui_curses.py` owns terminal input and presentation.
- `persistence.py` owns safe save/load behavior.
- `voice.py` owns the provider-neutral voice contract and adapters.
- `settings.py` owns non-secret local preferences and first-run setup.

## License

The game is MIT licensed. Bundled llama.cpp and SmolLM2 licenses are included in full release archives.
