"""
utils.py — Helper functions for the Carbon Footprint Assistant.

Covers: input validation, carbon calculations, output formatting,
suggestion generation, and data parsing. All functions are pure and
stateless so they can be tested in isolation.
"""

from __future__ import annotations

# ── Carbon emission factors ──────────────────────────────────────────────────
TRAVEL_FACTOR: float = 0.21        # kg CO₂ per km
ELECTRICITY_FACTOR: float = 0.82   # kg CO₂ per unit (kWh)
VEGETARIAN_MEAL_FACTOR: float = 1.0   # kg CO₂ per meal
NONVEG_MEAL_FACTOR: float = 3.0       # kg CO₂ per meal
RECYCLE_REDUCTION: float = 0.5     # kg CO₂ saved per recycling action

MAX_INPUT_LENGTH: int = 200        # guard against absurdly long inputs


# ── Input validation ─────────────────────────────────────────────────────────

def validate_input_length(text: str) -> bool:
    """Return True if *text* is within the allowed maximum length."""
    return len(text) <= MAX_INPUT_LENGTH


def parse_positive_number(token: str) -> float | None:
    """
    Try to parse *token* as a positive float.

    Returns the float value, or None if parsing fails or the value is
    not strictly positive.
    """
    try:
        value = float(token)
        if value > 0:
            return value
        return None
    except (ValueError, TypeError):
        return None


def parse_meal_type(token: str) -> str | None:
    """
    Normalise *token* to a canonical meal type string.

    Recognised aliases
    ------------------
    vegetarian / veg / plant  →  ``"vegetarian"``
    nonveg / non-veg / meat / non_veg  →  ``"nonveg"``

    Returns None for anything else.
    """
    normalised = token.strip().lower()
    if normalised in {"vegetarian", "veg", "plant"}:
        return "vegetarian"
    if normalised in {"nonveg", "non-veg", "meat", "non_veg"}:
        return "nonveg"
    return None


def parse_recycle_material(token: str) -> str | None:
    """
    Validate a recycling material keyword.

    Accepted materials: plastic, paper, glass, metal, cardboard.
    Returns the lower-cased material name, or None if unrecognised.
    """
    accepted = {"plastic", "paper", "glass", "metal", "cardboard"}
    normalised = token.strip().lower()
    return normalised if normalised in accepted else None


# ── Carbon calculations ───────────────────────────────────────────────────────

def calculate_travel_emission(km: float) -> float:
    """Return CO₂ emission in kg for *km* kilometres of travel."""
    return round(km * TRAVEL_FACTOR, 4)


def calculate_electricity_emission(units: float) -> float:
    """Return CO₂ emission in kg for *units* electricity units consumed."""
    return round(units * ELECTRICITY_FACTOR, 4)


def calculate_meal_emission(count: float, meal_type: str) -> float:
    """
    Return CO₂ emission in kg for *count* meals of *meal_type*.

    Raises ValueError for an unknown meal type.
    """
    if meal_type == "vegetarian":
        return round(count * VEGETARIAN_MEAL_FACTOR, 4)
    if meal_type == "nonveg":
        return round(count * NONVEG_MEAL_FACTOR, 4)
    raise ValueError(f"Unknown meal type: {meal_type!r}")


def calculate_recycle_reduction() -> float:
    """Return the fixed CO₂ reduction in kg for one recycling action."""
    return RECYCLE_REDUCTION


# ── Output formatting ─────────────────────────────────────────────────────────

def format_emission(kg: float) -> str:
    """Format a CO₂ value for display, e.g. ``'2.10 kg CO₂'``."""
    return f"{kg:.2f} kg CO\u2082"


def format_activity_line(activity: dict) -> str:
    """
    Render a single activity dictionary as a human-readable string.

    Expected keys: ``type``, ``detail``, ``emission``.
    """
    activity_type = activity.get("type", "unknown").capitalize()
    detail = activity.get("detail", "")
    emission = activity.get("emission", 0.0)
    sign = "-" if emission < 0 else "+"
    return f"  • {activity_type:<14} {detail:<28} {sign}{format_emission(abs(emission))}"


def build_summary(activities: list[dict], total: float) -> str:
    """
    Build a multiline summary string from a list of activity dicts.

    Parameters
    ----------
    activities:
        List of activity records produced by the assistant.
    total:
        Running total CO₂ in kg (may be negative after recycling).
    """
    if not activities:
        return "  No activities recorded yet. Start by logging travel, meals, or electricity!"

    lines = ["  Activity Log:", "  " + "─" * 58]
    for act in activities:
        lines.append(format_activity_line(act))
    lines.append("  " + "─" * 58)
    lines.append(f"  Total carbon footprint: {format_emission(max(total, 0.0))}")
    return "\n".join(lines)


# ── Suggestion generation ─────────────────────────────────────────────────────

_TIPS: list[str] = [
    "🚶 Walk or cycle for short trips to cut travel emissions.",
    "🌿 Swap one non-veg meal per day for a vegetarian option.",
    "💡 Switch to LED bulbs — they use up to 80 % less electricity.",
    "♻️  Recycle plastic, paper, and glass regularly to offset emissions.",
    "🚌 Use public transport instead of a private car when possible.",
    "🌱 Plant a tree or support a local reforestation project.",
    "🥦 Buy local, seasonal produce to reduce food transport emissions.",
    "📵 Unplug electronics when not in use to cut standby power.",
    "🌤️  Air-dry clothes instead of using a tumble dryer.",
    "🛒 Bring reusable bags and containers to reduce plastic waste.",
]


def get_tips(n: int = 3) -> list[str]:
    """Return the first *n* tips from the curated tip list."""
    return _TIPS[:max(1, n)]


def generate_personalised_suggestions(total_emission: float) -> list[str]:
    """
    Return targeted suggestions based on the session's total emission.

    Thresholds are intentionally coarse so users see actionable advice
    without needing detailed category breakdowns.
    """
    suggestions: list[str] = []

    if total_emission > 20:
        suggestions.append(
            "🔴 Your footprint is high. Consider switching to public transport and reducing meat consumption."
        )
    elif total_emission > 10:
        suggestions.append(
            "🟡 You're above average. Small changes like one fewer non-veg meal per week can help."
        )
    else:
        suggestions.append(
            "🟢 Great job keeping your footprint low! Keep recycling and choosing plant-based meals."
        )

    suggestions.append("💡 Tip: Even a 10 % reduction in electricity usage can save ~15 kg CO₂ per month.")
    return suggestions