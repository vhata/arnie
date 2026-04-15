# Arnie

Desk workout notifications powered by Arnold Schwarzenegger's *Get Back In Shape* guide. A macOS LaunchAgent nudges you every 30 minutes during work hours with a quick exercise you can do at your desk.

## How it works

Exercises are organized into three tiers that unlock over time:

- **Tier 1 (Weeks 1–2):** The gentlest start — chair squats, wall pushups, marching in place, calf raises, desk planks, stretches
- **Tier 2 (Weeks 3–4):** Adds bodyweight squats, desk pushups, wall sits, lunges, glute bridges, step-ups
- **Tier 3 (Week 5+):** The full pool — slow tempo reps, 2-minute challenges, myo-reps, mountain climbers, and more

Within a day, exercises don't repeat until the full eligible pool has been shown. Each notification includes a motivational quote.

## Setup

```bash
python arnie.py install
```

This creates a virtual environment, initializes state, and installs a macOS LaunchAgent that fires every 30 minutes from 10:00 to 18:30.

## Commands

```
python arnie.py notify [--force]   # Fire one notification now (--force ignores work hours)
python arnie.py install            # Install the LaunchAgent
python arnie.py uninstall          # Remove the LaunchAgent (keeps state and logs)
python arnie.py status             # Show current tier, day count, and today's exercises
python arnie.py log                # Print today's exercise log
python arnie.py reset              # Reset progression back to tier 1, day 1
```

## Requirements

- macOS
- Python 3 (Homebrew or system)

No third-party packages — stdlib only.

## Files

```
arnie.py        # CLI and notification logic
exercises.py    # Exercise data, selection, and progression
data/
  state.json    # Tracks current tier and today's shown exercises (auto-created)
  logs/         # Daily exercise logs (auto-created)
```
