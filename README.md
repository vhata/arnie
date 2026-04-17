# Arnie

Desk workout notifications powered by Arnold Schwarzenegger's *Get Back In Shape* guide. A native macOS menu bar app that nudges you with exercises throughout the workday.

Built with Claude Code.

## Features

- **Menu bar app** with status, settings, and today's exercise log
- **Interactive notifications** with Done, Skip, and Another buttons
- **49 exercises** across 3 tiers that unlock over weeks
- **Configurable** schedule, frequency, sounds, and progression
- **Start at Login** support

## Quick start

```bash
python arnie.py install
open Arnie.app
```

Or just build and launch `Arnie.app` — it's self-contained and handles its own scheduling.

## How it works

Exercises are organized into three tiers that unlock over time:

- **Tier 1 (Weeks 1–2):** 12 exercises — chair squats, wall pushups, marching in place, calf raises, desk planks, cat camel, bird dog, IYT raises, stretches
- **Tier 2 (Weeks 3–4):** 13 more (25 total) — bodyweight squats, desk pushups, wall sits, lunges, glute bridges, step-ups, leg raises, spiderman lunges
- **Tier 3 (Week 5+):** 24 more (49 total) — slow tempo reps, 2-minute challenges, myo-reps, the countdown, squat jumps, isometric holds, bear crawls, and more

Within a day, exercises don't repeat until the full eligible pool has been shown. Each notification includes a motivational quote.

## The menu bar app

Click the walking figure icon in your menu bar to see:

- Last exercise shown
- "Next Exercise" button (or press ⌘N)
- Current day, tier, and exercise count
- Today's exercise log
- Settings (hours, frequency, sound, Start at Login)
- Reset progression

Notifications have action buttons: **Done** (default), **Skip** (lets the exercise come back later), and **Another** (fires a new one immediately).

## Python CLI

The CLI reads and writes the same data as the app.

```
python arnie.py install            # Build Arnie.app and install LaunchAgent
python arnie.py notify [--force]   # Fire one notification now
python arnie.py status             # Show current state and schedule
python arnie.py log                # Print today's exercise log
python arnie.py config [options]   # View or update configuration
python arnie.py reset              # Reset progression back to tier 1, day 1
python arnie.py export-exercises   # Regenerate exercises.json from Python data
python arnie.py uninstall          # Remove the LaunchAgent
```

## Configuration

Change settings via the menu bar app's Settings submenu, or via CLI:

```bash
python arnie.py config --start-hour 9 --end-hour 18
python arnie.py config --frequency 45
python arnie.py config --tier-days 7,7
python arnie.py config --sound Glass
```

| Setting | Default | Description |
|---------|---------|-------------|
| `start_hour` | 10 | Hour to start notifications (0–23) |
| `end_hour` | 19 | Hour to stop notifications (0–23) |
| `frequency_minutes` | 30 | Minutes between notifications |
| `tier_days` | [14, 14] | Days at each tier before unlocking the next |
| `sound` | Ping | macOS notification sound name |

## Data storage

App data lives in `~/Library/Application Support/Arnie/`:

```
config.json     # User settings
state.json      # Tier progression and today's shown exercises
logs/           # Daily exercise logs
```

## Building from source

Requires macOS 14+ and Xcode Command Line Tools.

```bash
python arnie.py install    # Builds Arnie.app, installs LaunchAgent
```

Or manually:

```bash
python arnie.py export-exercises
swiftc -o Arnie.app/Contents/MacOS/Arnie notifier/*.swift \
  -framework Cocoa -framework UserNotifications -framework ServiceManagement \
  -target arm64-apple-macosx14.0
cp notifier/Info.plist Arnie.app/Contents/Info.plist
mkdir -p Arnie.app/Contents/Resources
cp exercises.json Arnie.app/Contents/Resources/exercises.json
codesign --force --sign - Arnie.app
```

## TODO

### Sort the IP story before distributing

Exercise names and instructions in `exercises.json` are derived from Arnold Schwarzenegger's *Get Back In Shape* guide (distributed via the Pump Club newsletter). Workout names like "The 20-Second Burn" and "The Pain Reliever" come straight from the guide's table of contents, and instructions are paraphrased from the workout descriptions.

For personal use this is fine. Before shipping this to anyone else, pick one:

- Rewrite every `name` and `instruction` in original language, and drop the `source` field.
- Reach out to Arnold's Pump Club team for permission or a licensing arrangement.

### Proper progression

The current tier system gates exercises behind wall-clock days (14 days at Tier 1, 14 at Tier 2, then all unlocked). With the default schedule that means each Tier 1 exercise repeats ~20+ times before anything new appears — which makes the app boring fast, working against its own goal of nudging you to move.

Better model to design:

- Progression should respond to *use*, not the calendar. Unlock new exercises after N completed reps, not N days.
- Track per-exercise completion counts in state, separate from `today_shown`.
- Give the user a sense of "moving forward" on every `Done` tap.
- Consider dropping tiers entirely and replacing them with tags (`easy`/`medium`/`hard`, or `chair`/`standing`/`floor`) that the user can filter on.

#### Sub-note: gamification

If we keep something progression-shaped, gamification can help it stick:

- **Streaks** — consecutive days with at least one `Done`. Show it in the menu.
- **Daily goal** — a small target (e.g. 5 exercises/day). Progress bar in the menu.
- **Unlock events** — when a new exercise becomes available, fire a distinct "New exercise unlocked!" notification so it feels like a reward, not just a larger pool.
- **Weekly summary** — a Sunday notification with the week's count, best day, new unlocks.
- **Careful with guilt mechanics** — skips shouldn't punish. The app should feel like a cheerful nudge, not Duolingo's owl. Losing a streak over one bad day is the kind of thing that makes people uninstall.

## Files

```
notifier/
  main.swift                # App entry point, backward compat with CLI
  MenuBarController.swift   # Menu bar icon and dropdown
  NotificationManager.swift # Notifications with action buttons
  ExerciseEngine.swift      # Exercise loading, tier logic, selection
  DataManager.swift         # Config, state, and log I/O
  TimerController.swift     # Exercise scheduling
  Info.plist                # App bundle metadata
exercises.json              # Shared exercise data (generated from Python)
exercises.py                # Python exercise loader and logic
arnie.py                    # Python CLI
config.py                   # Python config management
```
