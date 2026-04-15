#!/usr/bin/env python3
"""
Arnie — Desk workout notifications from Arnold's Get Back In Shape guide.

Usage:
    python arnie.py notify [--force]   Fire one notification now
    python arnie.py install            Install the LaunchAgent (every 30 min, 10am-7pm)
    python arnie.py uninstall          Remove the LaunchAgent
    python arnie.py status             Show current state and schedule
    python arnie.py log                Print today's exercise log
    python arnie.py reset              Reset progression to day 1
"""

import argparse
import json
import os
import plistlib
import subprocess
import sys
import tempfile
from datetime import date, datetime
from pathlib import Path

from exercises import (
    EXERCISES,
    days_until_next_tier,
    get_current_tier,
    pick_exercise,
    pick_quote,
)

PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"
LOGS_DIR = DATA_DIR / "logs"
STATE_FILE = DATA_DIR / "state.json"
VENV_DIR = PROJECT_DIR / ".venv"
PLIST_NAME = "com.arnie.workout"
PLIST_DEST = Path.home() / "Library" / "LaunchAgents" / f"{PLIST_NAME}.plist"

WORK_START_HOUR = 10
WORK_END_HOUR = 19  # 7pm — last notification at 18:30


# --- State management ---

def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return default_state()


def default_state() -> dict:
    return {
        "tier_start_date": date.today().isoformat(),
        "last_date": None,
        "today_shown": [],
    }


def save_state(state: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    # Atomic write
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2))
    tmp.replace(STATE_FILE)


# --- Notification ---

def send_notification(title: str, message: str):
    # osascript notification strings need quotes escaped
    safe_title = title.replace('"', '\\"')
    safe_msg = message.replace('"', '\\"')
    subprocess.run(
        [
            "osascript", "-e",
            f'display notification "{safe_msg}" with title "{safe_title}" sound name "Ping"',
        ],
        check=True,
    )


def append_log(exercise: dict, quote: str):
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_DIR / f"{date.today().isoformat()}.log"
    timestamp = datetime.now().strftime("%H:%M")
    line = f"{timestamp}  {exercise['name']} — {exercise['instruction']}\n"
    with open(log_file, "a") as f:
        f.write(line)


# --- Commands ---

def cmd_notify(args):
    now = datetime.now()
    if not args.force and not (WORK_START_HOUR <= now.hour < WORK_END_HOUR):
        return  # Outside work hours, exit silently

    state = load_state()

    # New day? Reset today's shown list
    today = date.today().isoformat()
    if state.get("last_date") != today:
        state["today_shown"] = []
        state["last_date"] = today

    exercise = pick_exercise(state)
    quote = pick_quote()

    title = f"Arnie: {exercise['name']}"
    body = f"{exercise['instruction']}\n\n{quote}"

    send_notification(title, body)
    append_log(exercise, quote)

    state["today_shown"].append(exercise["id"])
    save_state(state)

    print(f"[Arnie] {exercise['name']}")
    print(f"  {exercise['instruction']}")
    print(f"  (from: {exercise['source']})")
    print(f"  \"{quote}\"")


def cmd_install(args):
    # Create data directories
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # Initialize state if needed
    if not STATE_FILE.exists():
        save_state(default_state())
        print(f"Initialized state (tier 1, starting today)")

    # Create venv for a stable Python path
    if not VENV_DIR.exists():
        print("Creating virtual environment...")
        subprocess.run(
            [sys.executable, "-m", "venv", str(VENV_DIR)],
            check=True,
        )
        print(f"  Created at {VENV_DIR}")
    else:
        print(f"Venv already exists at {VENV_DIR}")

    venv_python = VENV_DIR / "bin" / "python3"

    # Generate plist
    intervals = []
    for hour in range(WORK_START_HOUR, WORK_END_HOUR):
        for minute in (0, 30):
            intervals.append({"Hour": hour, "Minute": minute})

    plist = {
        "Label": PLIST_NAME,
        "ProgramArguments": [
            str(venv_python),
            str(PROJECT_DIR / "arnie.py"),
            "notify",
        ],
        "StartCalendarInterval": intervals,
        "StandardOutPath": str(DATA_DIR / "launchd.stdout.log"),
        "StandardErrorPath": str(DATA_DIR / "launchd.stderr.log"),
        "WorkingDirectory": str(PROJECT_DIR),
    }

    # Write plist to LaunchAgents
    PLIST_DEST.parent.mkdir(parents=True, exist_ok=True)
    with open(PLIST_DEST, "wb") as f:
        plistlib.dump(plist, f)
    print(f"Wrote plist to {PLIST_DEST}")

    # Load the agent
    subprocess.run(["launchctl", "unload", str(PLIST_DEST)], capture_output=True)
    subprocess.run(["launchctl", "load", str(PLIST_DEST)], check=True)
    print(f"LaunchAgent loaded. Notifications every 30 min, {WORK_START_HOUR}:00-{WORK_END_HOUR - 1}:30.")
    print()
    print("Test it now with: python arnie.py notify --force")


def cmd_uninstall(args):
    if PLIST_DEST.exists():
        subprocess.run(["launchctl", "unload", str(PLIST_DEST)], capture_output=True)
        PLIST_DEST.unlink()
        print("LaunchAgent unloaded and removed.")
    else:
        print("LaunchAgent not installed.")
    print("(State and logs have been kept.)")


def cmd_status(args):
    # LaunchAgent status
    result = subprocess.run(
        ["launchctl", "list"],
        capture_output=True, text=True,
    )
    agent_loaded = PLIST_NAME in result.stdout
    print(f"LaunchAgent: {'loaded' if agent_loaded else 'not loaded'}")

    # State
    state = load_state()
    tier = get_current_tier(state["tier_start_date"])
    remaining = days_until_next_tier(state["tier_start_date"])
    start = state["tier_start_date"]
    days_active = (date.today() - date.fromisoformat(start)).days

    print(f"Day: {days_active + 1} (started {start})")
    print(f"Current tier: {tier} of 3")
    if remaining is not None:
        print(f"Next tier in: {remaining} days")
    else:
        print("All tiers unlocked!")

    eligible = [e for e in EXERCISES if e["tier"] <= tier]
    shown_today = len(state.get("today_shown", []))
    print(f"Exercises today: {shown_today} / {len(eligible)} available")

    # Today's log
    log_file = LOGS_DIR / f"{date.today().isoformat()}.log"
    if log_file.exists():
        print(f"\nToday's log ({log_file.name}):")
        print(log_file.read_text())


def cmd_log(args):
    log_file = LOGS_DIR / f"{date.today().isoformat()}.log"
    if log_file.exists():
        print(log_file.read_text(), end="")
    else:
        print("No exercises logged today.")


def cmd_reset(args):
    state = load_state()
    state["tier_start_date"] = date.today().isoformat()
    state["today_shown"] = []
    state["last_date"] = None
    save_state(state)
    print("Progression reset to tier 1, day 1. Fresh start!")


# --- CLI ---

def main():
    parser = argparse.ArgumentParser(
        prog="arnie",
        description="Desk workout notifications from Arnold's Get Back In Shape guide.",
    )
    sub = parser.add_subparsers(dest="command")

    notify_p = sub.add_parser("notify", help="Fire one notification now")
    notify_p.add_argument("--force", action="store_true", help="Ignore work hours check")

    sub.add_parser("install", help="Install the LaunchAgent")
    sub.add_parser("uninstall", help="Remove the LaunchAgent")
    sub.add_parser("status", help="Show current state and schedule")
    sub.add_parser("log", help="Print today's exercise log")
    sub.add_parser("reset", help="Reset progression to day 1")

    args = parser.parse_args()

    commands = {
        "notify": cmd_notify,
        "install": cmd_install,
        "uninstall": cmd_uninstall,
        "status": cmd_status,
        "log": cmd_log,
        "reset": cmd_reset,
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
