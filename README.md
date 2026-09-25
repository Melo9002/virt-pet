# virt-pet 🐣

A cozy, real-time virtual pet that lives in your terminal.

No graphics engine. No AI. Just a tiny creature, a clock that keeps moving, and the consequences of care (or neglect). The code stays deliberately small, readable, and hackable.

## Features

- Continuous real-time simulation rather than turns
- Animated ASCII pet, color-coded care meters, moods, and event log
- Six wellbeing states: content, hungry, lonely, dirty, sleepy, and sick
- Feed, play, sleep, wake, tidy, pause, and chat actions
- A deterministic offline personality behind a provider-independent voice interface
- Sleep slows hunger and protects happiness while age continues
- Persistent state with safe, atomic saves
- Responsive curses UI with a helpful minimum-size screen

## Run it

Requires Python 3.10 or newer. On Windows, the conditional dependency installs `windows-curses`.

```bash
pip install -r requirements.txt
python -m virtpet.main
```

Or install an editable command:

```bash
pip install -e .
virt-pet
```

The interface needs a terminal at least 64 columns wide and 27 rows tall.

To accelerate the simulation to one in-game hour per real second while balancing it:

```bash
python -m virtpet.main --debug
```

## Controls

| Key | Action |
| ---: | :--- |
| `f` | Feed (while awake) |
| `p` | Play (while awake) |
| `s` | Sleep / wake |
| `t` | Tidy up |
| `c` | Talk to your pet (`Enter` sends, `Esc` cancels) |
| `space` | Pause / resume time |
| `q` | Save and quit |

## How it works

`Pet` owns the state and rules, `GameEngine` translates elapsed time and player intent into changes, `CursesUI` renders and accepts input, and `persistence` handles JSON saves. `PetVoice` is the small provider-neutral boundary for dialogue; the built-in `FallbackVoice` works without a model, network, or API key. Those boundaries are intentional.

State is saved after time advances and after every action. The pet remembers its age, needs, activity, pause state, and internal timers. If a save is invalid, it is preserved as `pet_save.json.corrupt` and a new pet is created.

Run the tests locally with:

```bash
python -m unittest discover -v
```

Every push and pull request also runs the suite automatically on Windows and Linux with Python 3.10 and 3.13.
