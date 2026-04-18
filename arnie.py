#!/usr/bin/env python3
"""
Arnie — Desk workout notifications from Arnold's Get Back In Shape guide.

Usage:
    python arnie.py install            Build Arnie.app (no LaunchAgent)
    python arnie.py install-agent      Install the LaunchAgent scheduler
    python arnie.py notify [--force]   Fire one notification now
    python arnie.py status             Show current state and schedule
    python arnie.py log                Print today's exercise log
    python arnie.py config [options]   View or update configuration
    python arnie.py reset              Reset progression to day 1
    python arnie.py uninstall          Remove the LaunchAgent
    python arnie.py export-exercises   Export exercises.json from Python data
"""

import argparse
import json
import os
import plistlib
import shutil
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

from config import APP_SUPPORT_DIR, load_config, save_config, validate_config
from exercises import (
    EXERCISES,
    QUOTES,
    days_until_next_tier,
    get_current_tier,
    pick_exercise,
    pick_quote,
)

PROJECT_DIR = Path(__file__).resolve().parent
LOGS_DIR = APP_SUPPORT_DIR / "logs"
STATE_FILE = APP_SUPPORT_DIR / "state.json"
VENV_DIR = PROJECT_DIR / ".venv"
PLIST_NAME = "com.arnie.workout"
PLIST_DEST = Path.home() / "Library" / "LaunchAgents" / f"{PLIST_NAME}.plist"
NOTIFIER_APP = PROJECT_DIR / "Arnie.app"
NOTIFIER_BIN = NOTIFIER_APP / "Contents" / "MacOS" / "Arnie"

SWIFT_SOURCES = [
    "notifier/main.swift",
    "notifier/DataManager.swift",
    "notifier/ExerciseEngine.swift",
    "notifier/NotificationManager.swift",
    "notifier/TimerController.swift",
    "notifier/MenuBarController.swift",
]


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
    APP_SUPPORT_DIR.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2))
    tmp.replace(STATE_FILE)


# --- Notification ---

def send_notification(title: str, message: str, sound: str):
    if NOTIFIER_BIN.exists():
        subprocess.run(
            ["open", str(NOTIFIER_APP), "--args", title, message, sound],
            check=True,
        )
    else:
        safe_title = title.replace('"', '\\"')
        safe_msg = message.replace('"', '\\"')
        safe_sound = sound.replace('"', '\\"')
        subprocess.run(
            [
                "osascript", "-e",
                f'display notification "{safe_msg}" with title "{safe_title}" sound name "{safe_sound}"',
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
    config = load_config()
    now = datetime.now()
    if not args.force:
        if not (config["start_hour"] <= now.hour < config["end_hour"]):
            return
        if config["weekdays_only"] and now.weekday() >= 5:
            return

    state = load_state()

    today = date.today().isoformat()
    if state.get("last_date") != today:
        state["today_shown"] = []
        state["last_date"] = today

    exercise = pick_exercise(state, config["tier_days"])
    quote = pick_quote()

    title = f"Arnie: {exercise['name']}"
    body = f"{exercise['instruction']}\n\n{quote}"

    send_notification(title, body, config["sound"])
    append_log(exercise, quote)

    state["today_shown"].append(exercise["id"])
    save_state(state)

    print(f"[Arnie] {exercise['name']}")
    print(f"  {exercise['instruction']}")
    print(f"  (from: {exercise['source']})")
    print(f"  \"{quote}\"")


def cmd_export_exercises(args):
    """Export exercises.json from Python exercise data."""
    out = PROJECT_DIR / "exercises.json"
    data = {"exercises": EXERCISES, "quotes": QUOTES}
    out.write_text(json.dumps(data, indent=2) + "\n")
    print(f"Exported {len(EXERCISES)} exercises and {len(QUOTES)} quotes to {out}")


def build_notifier():
    """Compile all Swift sources into Arnie.app."""
    exercises_json = PROJECT_DIR / "exercises.json"
    if not exercises_json.exists():
        print("Generating exercises.json...")
        cmd_export_exercises(None)

    print("Building Arnie.app...")
    NOTIFIER_BIN.parent.mkdir(parents=True, exist_ok=True)

    src_paths = [str(PROJECT_DIR / s) for s in SWIFT_SOURCES]
    subprocess.run(
        [
            "swiftc", "-o", str(NOTIFIER_BIN),
            *src_paths,
            "-framework", "Cocoa",
            "-framework", "UserNotifications",
            "-framework", "ServiceManagement",
            "-target", "arm64-apple-macosx14.0",
        ],
        check=True,
    )

    # Copy Info.plist
    shutil.copy2(
        str(PROJECT_DIR / "notifier" / "Info.plist"),
        str(NOTIFIER_APP / "Contents" / "Info.plist"),
    )

    # Copy exercises.json into bundle Resources
    resources_dir = NOTIFIER_APP / "Contents" / "Resources"
    resources_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(exercises_json), str(resources_dir / "exercises.json"))

    # Ad-hoc codesign
    subprocess.run(["codesign", "--force", "--sign", "-", str(NOTIFIER_APP)], check=True)
    print(f"  Built and signed {NOTIFIER_APP}")


def cmd_install(args):
    """Build Arnie.app and set up data directories. Does not touch the LaunchAgent."""
    build_notifier()

    APP_SUPPORT_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    if not STATE_FILE.exists():
        save_state(default_state())
        print("Initialized state (tier 1, starting today)")

    print()
    print(f"Arnie.app built at {NOTIFIER_APP}")
    print("Launch it directly — it runs its own menu bar timer.")
    print("If you'd rather schedule via launchd, run 'python arnie.py install-agent'.")


def cmd_install_agent(args):
    """Install the LaunchAgent that fires notifications via the Python CLI."""
    config = load_config()

    APP_SUPPORT_DIR.mkdir(parents=True, exist_ok=True)

    if not VENV_DIR.exists():
        print("Creating virtual environment...")
        subprocess.run(
            [sys.executable, "-m", "venv", str(VENV_DIR)],
            check=True,
        )
        print(f"  Created at {VENV_DIR}")

    venv_python = VENV_DIR / "bin" / "python3"

    freq = config["frequency_minutes"]
    intervals = []
    for hour in range(config["start_hour"], config["end_hour"]):
        minute = 0
        while minute < 60:
            intervals.append({"Hour": hour, "Minute": minute})
            minute += freq

    plist = {
        "Label": PLIST_NAME,
        "ProgramArguments": [
            str(venv_python),
            str(PROJECT_DIR / "arnie.py"),
            "notify",
        ],
        "StartCalendarInterval": intervals,
        "StandardOutPath": str(APP_SUPPORT_DIR / "launchd.stdout.log"),
        "StandardErrorPath": str(APP_SUPPORT_DIR / "launchd.stderr.log"),
        "WorkingDirectory": str(PROJECT_DIR),
    }

    PLIST_DEST.parent.mkdir(parents=True, exist_ok=True)
    with open(PLIST_DEST, "wb") as f:
        plistlib.dump(plist, f)

    subprocess.run(["launchctl", "unload", str(PLIST_DEST)], capture_output=True)
    subprocess.run(["launchctl", "load", str(PLIST_DEST)], check=True)
    print(f"LaunchAgent loaded (every {freq} min, {config['start_hour']}:00-{config['end_hour'] - 1}:30)")
    print()
    print("Warning: if Arnie.app is also running, you'll get duplicate notifications.")


def cmd_uninstall(args):
    if PLIST_DEST.exists():
        subprocess.run(["launchctl", "unload", str(PLIST_DEST)], capture_output=True)
        PLIST_DEST.unlink()
        print("LaunchAgent unloaded and removed.")
    else:
        print("LaunchAgent not installed.")
    print("(State and logs have been kept.)")


def cmd_status(args):
    config = load_config()

    result = subprocess.run(["launchctl", "list"], capture_output=True, text=True)
    agent_loaded = PLIST_NAME in result.stdout
    print(f"LaunchAgent: {'loaded' if agent_loaded else 'not loaded'}")

    print(f"Schedule: every {config['frequency_minutes']} min, {config['start_hour']}:00-{config['end_hour'] - 1}:30")
    tier_days_str = " + ".join(f"{d}d" for d in config["tier_days"])
    print(f"Tier durations: {tier_days_str} (then all unlocked)")
    print(f"Sound: {config['sound']}")
    print(f"Data: {APP_SUPPORT_DIR}")

    state = load_state()
    tier = get_current_tier(state["tier_start_date"], config["tier_days"])
    remaining = days_until_next_tier(state["tier_start_date"], config["tier_days"])
    start = state["tier_start_date"]
    days_active = (date.today() - date.fromisoformat(start)).days
    num_tiers = len(config["tier_days"]) + 1

    print(f"\nDay: {days_active + 1} (started {start})")
    print(f"Current tier: {tier} of {num_tiers}")
    if remaining is not None:
        print(f"Next tier in: {remaining} days")
    else:
        print("All tiers unlocked!")

    eligible = [e for e in EXERCISES if e["tier"] <= tier]
    shown_today = len(state.get("today_shown", []))
    print(f"Exercises today: {shown_today} / {len(eligible)} available")

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


def cmd_config(args):
    config = load_config()
    changed = False

    if args.start_hour is not None:
        config["start_hour"] = args.start_hour
        changed = True
    if args.end_hour is not None:
        config["end_hour"] = args.end_hour
        changed = True
    if args.frequency is not None:
        config["frequency_minutes"] = args.frequency
        changed = True
    if args.tier_days is not None:
        config["tier_days"] = [int(d) for d in args.tier_days.split(",")]
        changed = True
    if args.sound is not None:
        config["sound"] = args.sound
        changed = True
    if args.weekdays_only is not None:
        config["weekdays_only"] = args.weekdays_only
        changed = True

    if changed:
        errors = validate_config(config)
        if errors:
            for e in errors:
                print(f"Error: {e}")
            sys.exit(1)
        save_config(config)
        print("Config updated:")
    else:
        print("Current config:")

    print(f"  start_hour:       {config['start_hour']}")
    print(f"  end_hour:         {config['end_hour']}")
    print(f"  frequency_minutes: {config['frequency_minutes']}")
    print(f"  tier_days:        {config['tier_days']}")
    print(f"  sound:            {config['sound']}")
    print(f"  weekdays_only:    {config['weekdays_only']}")

    if changed:
        timing_changed = any(x is not None for x in [args.start_hour, args.end_hour, args.frequency])
        if timing_changed:
            print("\nRun 'python arnie.py install' to apply the new schedule.")


# --- CLI ---

def main():
    parser = argparse.ArgumentParser(
        prog="arnie",
        description="Desk workout notifications from Arnold's Get Back In Shape guide.",
    )
    sub = parser.add_subparsers(dest="command")

    notify_p = sub.add_parser("notify", help="Fire one notification now")
    notify_p.add_argument("--force", action="store_true", help="Ignore work hours check")

    sub.add_parser("install", help="Build Arnie.app (no LaunchAgent)")
    sub.add_parser("install-agent", help="Install the LaunchAgent scheduler")
    sub.add_parser("uninstall", help="Remove the LaunchAgent")
    sub.add_parser("status", help="Show current state and schedule")
    sub.add_parser("log", help="Print today's exercise log")
    sub.add_parser("reset", help="Reset progression to day 1")
    sub.add_parser("export-exercises", help="Export exercises.json from Python data")

    config_p = sub.add_parser("config", help="View or update configuration")
    config_p.add_argument("--start-hour", type=int, dest="start_hour", help="Hour to start notifications (0-23)")
    config_p.add_argument("--end-hour", type=int, dest="end_hour", help="Hour to stop notifications (0-23)")
    config_p.add_argument("--frequency", type=int, help="Minutes between notifications")
    config_p.add_argument("--tier-days", dest="tier_days", help="Days per tier, comma-separated (e.g. 14,14)")
    config_p.add_argument("--sound", help="macOS notification sound name")
    config_p.add_argument("--weekdays-only", dest="weekdays_only", action=argparse.BooleanOptionalAction, help="Only fire on Mon-Fri")

    args = parser.parse_args()

    commands = {
        "notify": cmd_notify,
        "install": cmd_install,
        "install-agent": cmd_install_agent,
        "uninstall": cmd_uninstall,
        "status": cmd_status,
        "log": cmd_log,
        "reset": cmd_reset,
        "config": cmd_config,
        "export-exercises": cmd_export_exercises,
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
