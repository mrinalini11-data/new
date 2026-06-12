"""
assistant.py — Core logic for the Carbon Footprint Assistant.

Responsibilities
----------------
* Intent detection via keyword matching (no ML dependency).
* Session-scoped activity log stored in RAM.
* Dispatch to calculation helpers in utils.py.
* Response generation in plain English.
"""

from __future__ import annotations

from utils import (
    validate_input_length,
    parse_positive_number,
    parse_meal_type,
    parse_recycle_material,
    calculate_travel_emission,
    calculate_electricity_emission,
    calculate_meal_emission,
    calculate_recycle_reduction,
    format_emission,
    build_summary,
    get_tips,
    generate_personalised_suggestions,
)


class CarbonAssistant:
    """
    Stateful assistant that tracks carbon activities for a single session.

    All state is held in instance variables so multiple independent
    sessions can run simultaneously without interference.
    """

    def __init__(self) -> None:
        self._activities: list[dict] = []   # ordered log of all actions
        self._total_emission: float = 0.0   # running CO₂ total in kg

    # ── Public API ────────────────────────────────────────────────────────────

    def process(self, raw_input: str) -> str:
        """
        Parse *raw_input*, dispatch to the correct handler, and return a
        response string ready to print.

        This is the single entry-point used by main.py.
        """
        if not validate_input_length(raw_input):
            return "⚠️  Input is too long. Please keep commands under 200 characters."

        text = raw_input.strip()
        if not text:
            return "🤔 I didn't catch that. Type 'help' to see available commands."

        intent = self._detect_intent(text)

        handlers = {
            "travel":      self._handle_travel,
            "electricity": self._handle_electricity,
            "meals":       self._handle_meals,
            "recycle":     self._handle_recycle,
            "summary":     self._handle_summary,
            "tips":        self._handle_tips,
            "history":     self._handle_history,
            "unknown":     self._handle_unknown,
        }

        handler = handlers.get(intent, self._handle_unknown)
        return handler(text)

    def get_activities(self) -> list[dict]:
        """Return a shallow copy of the activity log."""
        return list(self._activities)

    def get_total_emission(self) -> float:
        """Return the current running CO₂ total in kg."""
        return self._total_emission

    # ── Intent detection ──────────────────────────────────────────────────────

    @staticmethod
    def _detect_intent(text: str) -> str:
        """
        Map user text to an intent string using simple keyword matching.

        Operates on lower-cased text so commands are case-insensitive.
        The first matching keyword wins; order therefore encodes priority.
        """
        lower = text.lower()

        keyword_map: list[tuple[str, str]] = [
            ("travel",      "travel"),
            ("electricity", "electricity"),
            ("meal",        "meals"),
            ("recycle",     "recycle"),
            ("summary",     "summary"),
            ("tip",         "tips"),
            ("history",     "history"),
        ]

        for keyword, intent in keyword_map:
            if keyword in lower:
                return intent

        return "unknown"

    # ── Command handlers ──────────────────────────────────────────────────────

    def _handle_travel(self, text: str) -> str:
        """
        Handle: ``travel <km> km``

        Adds a travel activity and returns a confirmation message.
        """
        tokens = text.lower().split()
        km_value = self._extract_number_from_tokens(tokens, after="travel")
        if km_value is None:
            return (
                "⚠️  I couldn't understand your travel command.\n"
                "    Usage: travel <km> km   (e.g. 'travel 20 km')"
            )

        emission = calculate_travel_emission(km_value)
        self._record_activity("travel", f"{km_value} km", emission)
        return (
            f"🚗 Logged {km_value} km of travel.\n"
            f"   Emission: {format_emission(emission)}\n"
            f"   Running total: {format_emission(max(self._total_emission, 0.0))}"
        )

    def _handle_electricity(self, text: str) -> str:
        """
        Handle: ``electricity <units> units``

        Adds an electricity activity and returns a confirmation message.
        """
        tokens = text.lower().split()
        units_value = self._extract_number_from_tokens(tokens, after="electricity")
        if units_value is None:
            return (
                "⚠️  I couldn't understand your electricity command.\n"
                "    Usage: electricity <units> units   (e.g. 'electricity 15 units')"
            )

        emission = calculate_electricity_emission(units_value)
        self._record_activity("electricity", f"{units_value} units", emission)
        return (
            f"💡 Logged {units_value} units of electricity.\n"
            f"   Emission: {format_emission(emission)}\n"
            f"   Running total: {format_emission(max(self._total_emission, 0.0))}"
        )

    def _handle_meals(self, text: str) -> str:
        """
        Handle: ``meals <count> vegetarian|nonveg``

        Adds a meals activity and returns a confirmation message.
        """
        tokens = text.lower().split()

        count_value: float | None = None
        meal_type: str | None = None

        # Scan tokens for a positive number and a recognised meal-type keyword
        for i, token in enumerate(tokens):
            if count_value is None:
                candidate = parse_positive_number(token)
                if candidate is not None:
                    count_value = candidate
                    continue
            if meal_type is None:
                candidate_type = parse_meal_type(token)
                if candidate_type is not None:
                    meal_type = candidate_type

        if count_value is None or meal_type is None:
            return (
                "⚠️  I couldn't understand your meals command.\n"
                "    Usage: meals <count> vegetarian|nonveg\n"
                "    Examples: 'meals 3 vegetarian'  /  'meals 2 nonveg'"
            )

        emission = calculate_meal_emission(count_value, meal_type)
        self._record_activity("meals", f"{count_value}x {meal_type}", emission)
        return (
            f"🍽️  Logged {count_value} {meal_type} meal(s).\n"
            f"   Emission: {format_emission(emission)}\n"
            f"   Running total: {format_emission(max(self._total_emission, 0.0))}"
        )

    def _handle_recycle(self, text: str) -> str:
        """
        Handle: ``recycle <material>``

        Reduces the total footprint and records the action.
        """
        tokens = text.lower().split()

        material: str | None = None
        for token in tokens:
            if token == "recycle":
                continue
            candidate = parse_recycle_material(token)
            if candidate is not None:
                material = candidate
                break

        if material is None:
            return (
                "⚠️  Please specify a material to recycle.\n"
                "    Accepted: plastic, paper, glass, metal, cardboard\n"
                "    Example: 'recycle plastic'"
            )

        reduction = calculate_recycle_reduction()
        # Negative emission = a saving
        self._record_activity("recycle", f"{material}", -reduction)
        return (
            f"♻️  Great! Logged recycling of {material}.\n"
            f"   CO₂ saved: {format_emission(reduction)}\n"
            f"   Running total: {format_emission(max(self._total_emission, 0.0))}"
        )

    def _handle_summary(self, _text: str) -> str:
        """Return a formatted summary of all recorded activities."""
        summary = build_summary(self._activities, self._total_emission)
        suggestions = generate_personalised_suggestions(self._total_emission)
        suggestion_block = "\n".join(f"  {s}" for s in suggestions)
        return (
            "📊 Carbon Footprint Summary\n"
            "  " + "═" * 58 + "\n"
            f"{summary}\n\n"
            "  Personalised suggestions:\n"
            f"{suggestion_block}"
        )

    def _handle_tips(self, _text: str) -> str:
        """Return a list of actionable eco tips."""
        tips = get_tips(5)
        tip_lines = "\n".join(f"  {i + 1}. {tip}" for i, tip in enumerate(tips))
        return f"🌱 Eco Tips to Reduce Your Footprint:\n{tip_lines}"

    def _handle_history(self, _text: str) -> str:
        """Return a compact chronological history of all commands."""
        if not self._activities:
            return "📜 No activities recorded yet this session."

        lines = ["📜 Session History:"]
        for idx, act in enumerate(self._activities, start=1):
            emission = act["emission"]
            sign = "-" if emission < 0 else "+"
            lines.append(
                f"  {idx:>2}. {act['type']:<14} {act['detail']:<28} "
                f"{sign}{format_emission(abs(emission))}"
            )
        return "\n".join(lines)

    def _handle_unknown(self, _text: str) -> str:
        """Catch-all for unrecognised commands."""
        return (
            "🤔 I didn't recognise that command.\n"
            "   Type 'help' to see all available commands."
        )

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _record_activity(self, activity_type: str, detail: str, emission: float) -> None:
        """Append an activity to the log and update the running total."""
        self._activities.append(
            {"type": activity_type, "detail": detail, "emission": emission}
        )
        self._total_emission = round(self._total_emission + emission, 4)

    @staticmethod
    def _extract_number_from_tokens(tokens: list[str], after: str) -> float | None:
        """
        Scan *tokens* for a positive number.

        If *after* is provided, only tokens that appear after the first
        occurrence of *after* are considered, which prevents accidentally
        matching numbers that appear before the command keyword.
        """
        start_index = 0
        for i, token in enumerate(tokens):
            if token == after:
                start_index = i + 1
                break

        for token in tokens[start_index:]:
            value = parse_positive_number(token)
            if value is not None:
                return value
        return None


# ── Module-level help text ────────────────────────────────────────────────────

HELP_TEXT = """
╔══════════════════════════════════════════════════════════════╗
║          🌍  Carbon Footprint Assistant — Help               ║
╠══════════════════════════════════════════════════════════════╣
║  Command                   Description                       ║
║  ──────────────────────    ─────────────────────────────── ║
║  travel <km> km            Log kilometres travelled          ║
║  electricity <n> units     Log electricity units consumed    ║
║  meals <n> vegetarian      Log vegetarian meals              ║
║  meals <n> nonveg          Log non-vegetarian meals          ║
║  recycle <material>        Log a recycling action            ║
║  summary                   View total footprint & tips       ║
║  tips                      Show eco-friendly tips            ║
║  history                   List all session activities       ║
║  help                      Show this help message            ║
║  exit / quit               Exit the assistant                ║
╚══════════════════════════════════════════════════════════════╝
  Accepted materials: plastic, paper, glass, metal, cardboard
"""