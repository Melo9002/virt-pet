# virt-pet 🐣

A small terminal-based **virtual pet** experiment written in Python.

This project explores a simple idea:  
**care, continuity, and responsibility under time constraints**.

No graphics. No AI (yet). Just a tiny creature, a clock that keeps ticking, and the player’s choices.

---

## ✨ What This Is

- A **command-line V-pet** inspired by classic Tamagotchi-style games
- Focused on **behavior and consequences**, not visual flair
- Designed to be simple, readable, and extensible
- Built as a foundation for future experiments (memory, personality, AI narration)

This is intentionally small. Shipping > dreaming.

---

## 🧠 Core Concepts

- Time advances every turn
- Neglect has consequences
- Care improves stability, not perfection
- The pet’s state is deterministic and inspectable
- No hidden magic — behavior is encoded in rules

The goal is not to simulate intelligence, but **continuity**.

---

## 🗂 Project Structure

```
virt-pet/
│
├─ README.md
├─ requirements.txt
├─ pyproject.toml
│
└─ virtpet/
   ├─ __init__.py
   ├─ main.py      # Entry point
   ├─ game.py      # Game loop & player interaction
   └─ pet.py       # Pet logic & internal state
```

Separation of concerns is intentional and non-negotiable.

---

## ▶ How to Run

### Using PyCharm (recommended)

1. Open the project
2. Make sure a Python interpreter (3.10+) is configured
3. Open `virtpet/main.py`
4. Click the green **Run ▶** button

### Using terminal

```bash
python -m virtpet.main
```

---

## 🎮 Available Actions

- `feed`  → reduces hunger, small happiness boost
- `play`  → trades energy for happiness
- `sleep` → restores energy
- `quit`  → exits the game (time does not rewind)

Each action advances time.

---

## 🛣 Planned Extensions

These are *intentional future steps*, not promises:

- Save/load pet state (JSON)
- Personality traits (lazy, needy, resilient, chaotic)
- Long-term scars from neglect
- AI-generated narration layered on top of deterministic mechanics
- Alternative frontends (TUI / GUI)

---

## ⚠ Philosophy Note

This project is **not**:
- a replacement for pets
- a replacement for children
- an emotional manipulation engine

It is a **care artifact** — a small, persistent responsibility that fits modern, unstable routines.

---

## 📜 License

MIT — do what you want.

---

Built with curiosity, restraint, and a slightly judgmental virtual grandma.
