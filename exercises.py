"""Exercise data, selection logic, and progression for Arnie."""

import json
import random
from datetime import date
from pathlib import Path

_EXERCISES_FILE = Path(__file__).resolve().parent / "exercises.json"


def _load_data():
    with open(_EXERCISES_FILE) as f:
        data = json.load(f)
    return data["exercises"], data["quotes"]


EXERCISES, QUOTES = _load_data()


def get_current_tier(tier_start_date: str, tier_days: list[int]) -> int:
    """Compute current tier based on days since start."""
    start = date.fromisoformat(tier_start_date)
    days_elapsed = (date.today() - start).days
    tier = 1
    cumulative = 0
    for duration in tier_days:
        cumulative += duration
        if days_elapsed >= cumulative:
            tier += 1
        else:
            break
    return tier


def days_until_next_tier(tier_start_date: str, tier_days: list[int]) -> int | None:
    """Days remaining until the next tier unlocks. None if already at max tier."""
    start = date.fromisoformat(tier_start_date)
    days_elapsed = (date.today() - start).days
    cumulative = 0
    for duration in tier_days:
        cumulative += duration
        if days_elapsed < cumulative:
            return cumulative - days_elapsed
    return None


def pick_exercise(state: dict, tier_days: list[int]) -> dict:
    """Pick a random exercise not yet shown today, respecting current tier."""
    tier = get_current_tier(state["tier_start_date"], tier_days)
    today_shown = state.get("today_shown", [])

    eligible = [e for e in EXERCISES if e["tier"] <= tier]
    pool = [e for e in eligible if e["id"] not in today_shown]

    if not pool:
        # All eligible exercises shown today — reset and pick from full pool
        state["today_shown"] = []
        pool = eligible

    return random.choice(pool)


def pick_quote() -> str:
    """Pick a random motivational quote."""
    return random.choice(QUOTES)
