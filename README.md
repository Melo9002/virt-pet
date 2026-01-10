# virt-pet (Proof of concept... I'll probably rebuild this in Godot at some point.) 🐣

A small terminal-based **real-time virtual pet** experiment written in Python.

This project explores a simple idea:  
**care, continuity, and responsibility under time constraints**.

No graphics. No AI (yet). Just a tiny creature, a clock that never stops, and the consequences of being present… or not.

---

## ✨ What This Is

- A **real-time terminal V-pet** inspired by Tamagotchi / Digimon-style games  
- Uses a **continuous clock** instead of turn-based actions  
- Features **persistent state** — your pet exists even after you quit  
- Designed to be **simple, readable, and hackable**
- Built as a foundation for future experiments (personality, memory, AI narration)

This is intentionally small.  
Shipping > dreaming.

---

## 🧠 Core Concepts

- Time advances automatically (real-time loop)
- The pet has **activity states** (idle, sleeping)
- **Pause** freezes time without altering behavior
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
   ├─ main.py          # Entry point & startup logic
   ├─ engine.py        # Real-time clock & ticking engine
   ├─ persistence.py  # Save / load (JSON)
   ├─ pet.py           # Pet state machine & rules
   └─ ui_curses.py     # Terminal UI (curses-based)
```

**Separation of concerns is intentional and non-negotiable.**

---

## ▶ How to Run

### Requirements

- Python **3.10+**
- On Windows: `windows-curses`

```bash
pip install -r requirements.txt
```

```bash
python -m virtpet.main
```

---

## 🎮 Controls

| Key | Action |
|----:|-------|
| `f` | Feed (idle only) |
| `p` | Play (idle only) |
| `s` | Sleep / Wake |
| `space` | Pause / Unpause time |
| `q` | Quit |

---

## 💾 Persistence

- State is saved automatically every tick
- Save file is ignored by git
- Your pet remembers its past

---

## 📜 License

MIT — do what you want.
