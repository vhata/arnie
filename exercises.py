"""Exercise data, selection logic, and progression for Arnie."""

import random
from datetime import date, datetime

# Days spent at each tier before unlocking the next
TIER_DURATIONS = [14, 14]  # 14 days at tier 1, 14 at tier 2, then tier 3 forever

EXERCISES = [
    # === TIER 1: Weeks 1-2 — the gentlest start ===
    {
        "id": "march_in_place",
        "name": "March in Place",
        "instruction": "Stand up and march with big steps, raising each thigh until it's perpendicular to your torso. 30 seconds.",
        "tier": 1,
        "source": "The 20-Second Burn",
    },
    {
        "id": "calf_raises",
        "name": "Standing Calf Raises",
        "instruction": "Stand up, rise onto your toes, lower back down. 20 reps. Arnold wouldn't let us skip calves.",
        "tier": 1,
        "source": "The 20-Second Burn",
    },
    {
        "id": "chair_squats",
        "name": "Chair Squats",
        "instruction": "Sit down on your chair, then stand back up without using your hands. 10 reps.",
        "tier": 1,
        "source": "The 20-Second Burn",
    },
    {
        "id": "wall_pushups",
        "name": "Wall Pushups",
        "instruction": "Place your hands on the wall at shoulder height and width. Do pushups against the wall. 10 reps.",
        "tier": 1,
        "source": "The 20-Second Burn",
    },
    {
        "id": "desk_plank",
        "name": "Desk Plank",
        "instruction": "Hands on your desk, body in a straight line from shoulders to ankles. Squeeze abs and glutes. Hold 20 seconds.",
        "tier": 1,
        "source": "The 20-Second Burn (Chair Plank)",
    },
    {
        "id": "bent_over_ys",
        "name": "Bent Over Y's",
        "instruction": "Push hips back, torso parallel to floor. Arms hanging down, lift them up at 45 degrees to form a Y. 10 reps.",
        "tier": 1,
        "source": "The 20-Second Burn",
    },
    {
        "id": "brettzel_stretch",
        "name": "The Brettzel Stretch",
        "instruction": "Lie on your right side, left knee across body held by right hand, grab right foot with left hand. Rotate left shoulder toward ground. 4-5 breaths each side.",
        "tier": 1,
        "source": "The Pain Reliever",
    },
    # === TIER 2: Weeks 3-4 — stepping it up ===
    {
        "id": "bodyweight_squats",
        "name": "Bodyweight Squats",
        "instruction": "Feet shoulder-width apart. Squat down as low as comfortable, stand back up. 10 reps.",
        "tier": 2,
        "source": "Multiple workouts",
    },
    {
        "id": "desk_pushups",
        "name": "Desk Pushups",
        "instruction": "Hands on your desk edge, body straight. Lower your chest to the desk and push back up. 8 reps.",
        "tier": 2,
        "source": "The 20-Second Burn (Incline Pushups)",
    },
    {
        "id": "wall_sit",
        "name": "Wall Sit",
        "instruction": "Back flat against the wall, slide down until thighs are parallel to the floor. Hold for 20 seconds.",
        "tier": 2,
        "source": "The Resistance Band Workout",
    },
    {
        "id": "reverse_lunges",
        "name": "Reverse Lunges",
        "instruction": "Step one foot back, lower your knee toward the floor, return to standing. Alternate legs. 5 per side.",
        "tier": 2,
        "source": "The Safest Way To Train To Failure",
    },
    {
        "id": "glute_bridge",
        "name": "Glute Bridge",
        "instruction": "Lie on the floor, knees bent, feet flat. Push hips up squeezing your glutes. Hold 3 seconds at top. 10 reps.",
        "tier": 2,
        "source": "Multiple workouts",
    },
    {
        "id": "step_ups",
        "name": "Step-Ups",
        "instruction": "Find a sturdy step or low bench. Step up, step down, alternate legs. 10 reps per leg.",
        "tier": 2,
        "source": "The 20-Second Burn",
    },
    {
        "id": "standing_hip_thrust",
        "name": "Standing Glute Squeeze",
        "instruction": "Stand with your back against the wall. Squeeze your glutes hard, pushing hips forward. Hold 10 seconds. Repeat 5 times.",
        "tier": 2,
        "source": "Adapted for desk",
    },
    # === TIER 3: Week 5+ — let's go ===
    {
        "id": "slow_squats",
        "name": "Slow Tempo Squats (5:3:1)",
        "instruction": "5 seconds to lower, hold the bottom 3 seconds, 1 second to stand. Harder than they sound. Just 3 reps.",
        "tier": 3,
        "source": "The Max Tension Workout",
    },
    {
        "id": "slow_desk_pushups",
        "name": "Slow Tempo Desk Pushups (5:3:1)",
        "instruction": "Hands on desk. 5 seconds down, hold at bottom 3 seconds, 1 second up. Just 3 reps.",
        "tier": 3,
        "source": "The Max Tension Workout",
    },
    {
        "id": "2min_squats",
        "name": "2-Minute Squat Challenge",
        "instruction": "Set a 2-minute timer. Do as many bodyweight squats as you can, resting when needed. Push yourself!",
        "tier": 3,
        "source": "The 2-Minute Muscle Challenge",
    },
    {
        "id": "2min_pushups",
        "name": "2-Minute Desk Pushup Challenge",
        "instruction": "Set a 2-minute timer. Do as many desk pushups as you can, resting when needed. Push yourself!",
        "tier": 3,
        "source": "The 2-Minute Muscle Challenge",
    },
    {
        "id": "myorep_squats",
        "name": "Myo-Rep Squats",
        "instruction": "15 bodyweight squats. Take 3-5 deep breaths. Do 3-5 more. Repeat the breathe-and-squat cycle 3 more times (5 sets total).",
        "tier": 3,
        "source": "Myo-Reps For Muscle",
    },
    {
        "id": "myorep_pushups",
        "name": "Myo-Rep Desk Pushups",
        "instruction": "15 desk pushups. Take 3-5 deep breaths. Do 3-5 more. Repeat the breathe-and-push cycle 3 more times (5 sets total).",
        "tier": 3,
        "source": "Myo-Reps For Muscle",
    },
    {
        "id": "mountain_climbers",
        "name": "Mountain Climbers",
        "instruction": "Hands on desk or floor, drive knees toward chest alternately. 20 seconds. Get that heart rate up!",
        "tier": 3,
        "source": "The 30-Second Full Body Blast",
    },
    {
        "id": "plank_walkout",
        "name": "Plank Walkout",
        "instruction": "Stand, bend forward, walk hands out to plank position, hold 2 seconds, walk hands back, stand. 5 reps.",
        "tier": 3,
        "source": "Reps, Reps, Reps",
    },
    {
        "id": "lateral_lunges",
        "name": "Lateral Lunges",
        "instruction": "Feet wide. Shift weight to one side, bending that knee, other leg straight. Alternate. 5 per side.",
        "tier": 3,
        "source": "Reps, Reps, Reps",
    },
    {
        "id": "hollow_body_hold",
        "name": "Hollow Body Hold",
        "instruction": "Lie on the floor, arms overhead, lift shoulders and legs off the ground. Hold 20 seconds. Great for your core.",
        "tier": 3,
        "source": "Reps, Reps, Reps",
    },
]

QUOTES = [
    "It is NEVER too late to start.",
    "Let's chase the pump together.",
    "Your body does NOT need weights to change; it requires resistance.",
    "Long workouts don't determine intensity.",
    "The fun part is the journey and watching yourself get better.",
    "More reps. That's the secret to success.",
    "No matter how out of shape, you can do this.",
    "A little movement now adds up to a big change.",
    "You don't need a gym. You just need to start.",
    "Come on, you can do this! Let's go!",
    "The last three or four reps is what makes the muscle grow.",
    "Strength does not come from winning.",
    "The mind is the limit.",
    "The worst thing you can do is nothing.",
    "Just remember, you can't climb the ladder of success with your hands in your pockets.",
]


def get_current_tier(tier_start_date: str) -> int:
    """Compute current tier based on days since start."""
    start = date.fromisoformat(tier_start_date)
    days_elapsed = (date.today() - start).days
    tier = 1
    cumulative = 0
    for duration in TIER_DURATIONS:
        cumulative += duration
        if days_elapsed >= cumulative:
            tier += 1
        else:
            break
    return tier


def days_until_next_tier(tier_start_date: str) -> int | None:
    """Days remaining until the next tier unlocks. None if already at max tier."""
    start = date.fromisoformat(tier_start_date)
    days_elapsed = (date.today() - start).days
    cumulative = 0
    for duration in TIER_DURATIONS:
        cumulative += duration
        if days_elapsed < cumulative:
            return cumulative - days_elapsed
    return None


def pick_exercise(state: dict) -> dict:
    """Pick a random exercise not yet shown today, respecting current tier."""
    tier = get_current_tier(state["tier_start_date"])
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
