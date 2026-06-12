"""
test_assistant.py — Unit tests for the Carbon Footprint Assistant.

Run with:
    python -m unittest test_assistant -v

All tests use only the Python standard-library unittest module.
"""

from __future__ import annotations

import unittest

from assistant import CarbonAssistant
from utils import (
    calculate_travel_emission,
    calculate_electricity_emission,
    calculate_meal_emission,
    calculate_recycle_reduction,
    parse_positive_number,
    parse_meal_type,
    parse_recycle_material,
    validate_input_length,
    generate_personalised_suggestions,
    get_tips,
    build_summary,
    format_emission,
    MAX_INPUT_LENGTH,
)


# ── utils.py tests ────────────────────────────────────────────────────────────

class TestTravelCalculation(unittest.TestCase):
    """Travel emission calculation (0.21 kg CO₂ / km)."""

    def test_basic(self):
        self.assertAlmostEqual(calculate_travel_emission(10), 2.1, places=4)

    def test_zero(self):
        self.assertEqual(calculate_travel_emission(0), 0.0)

    def test_large_distance(self):
        self.assertAlmostEqual(calculate_travel_emission(1000), 210.0, places=1)

    def test_fractional_km(self):
        result = calculate_travel_emission(0.5)
        self.assertAlmostEqual(result, 0.105, places=4)


class TestElectricityCalculation(unittest.TestCase):
    """Electricity emission calculation (0.82 kg CO₂ / unit)."""

    def test_basic(self):
        self.assertAlmostEqual(calculate_electricity_emission(10), 8.2, places=4)

    def test_zero(self):
        self.assertEqual(calculate_electricity_emission(0), 0.0)

    def test_fractional_units(self):
        result = calculate_electricity_emission(2.5)
        self.assertAlmostEqual(result, 2.05, places=4)


class TestMealCalculation(unittest.TestCase):
    """Meal emission calculations."""

    def test_vegetarian(self):
        self.assertAlmostEqual(calculate_meal_emission(3, "vegetarian"), 3.0, places=4)

    def test_nonveg(self):
        self.assertAlmostEqual(calculate_meal_emission(2, "nonveg"), 6.0, places=4)

    def test_unknown_meal_type_raises(self):
        with self.assertRaises(ValueError):
            calculate_meal_emission(1, "seafood")

    def test_single_vegetarian(self):
        self.assertEqual(calculate_meal_emission(1, "vegetarian"), 1.0)

    def test_single_nonveg(self):
        self.assertEqual(calculate_meal_emission(1, "nonveg"), 3.0)


class TestRecycleCalculation(unittest.TestCase):
    """Recycling reduction calculation."""

    def test_reduction_amount(self):
        self.assertEqual(calculate_recycle_reduction(), 0.5)

    def test_reduction_is_positive(self):
        self.assertGreater(calculate_recycle_reduction(), 0)


class TestInputValidation(unittest.TestCase):
    """Input length and number parsing."""

    def test_valid_length(self):
        self.assertTrue(validate_input_length("travel 10 km"))

    def test_too_long(self):
        long_input = "a" * (MAX_INPUT_LENGTH + 1)
        self.assertFalse(validate_input_length(long_input))

    def test_exact_max_length(self):
        exact = "a" * MAX_INPUT_LENGTH
        self.assertTrue(validate_input_length(exact))

    def test_parse_valid_number(self):
        self.assertEqual(parse_positive_number("42"), 42.0)

    def test_parse_float(self):
        self.assertAlmostEqual(parse_positive_number("3.5"), 3.5)

    def test_parse_negative_returns_none(self):
        self.assertIsNone(parse_positive_number("-5"))

    def test_parse_zero_returns_none(self):
        self.assertIsNone(parse_positive_number("0"))

    def test_parse_non_numeric_returns_none(self):
        self.assertIsNone(parse_positive_number("abc"))

    def test_parse_empty_returns_none(self):
        self.assertIsNone(parse_positive_number(""))


class TestMealTypeParsing(unittest.TestCase):
    """Meal type normalisation."""

    def test_vegetarian_alias(self):
        self.assertEqual(parse_meal_type("veg"), "vegetarian")

    def test_plant_alias(self):
        self.assertEqual(parse_meal_type("plant"), "vegetarian")

    def test_nonveg_alias(self):
        self.assertEqual(parse_meal_type("meat"), "nonveg")

    def test_non_veg_hyphenated(self):
        self.assertEqual(parse_meal_type("non-veg"), "nonveg")

    def test_unknown_returns_none(self):
        self.assertIsNone(parse_meal_type("sushi"))


class TestRecycleMaterialParsing(unittest.TestCase):
    """Recycling material validation."""

    def test_accepted_material(self):
        self.assertEqual(parse_recycle_material("plastic"), "plastic")

    def test_case_insensitive(self):
        self.assertEqual(parse_recycle_material("PAPER"), "paper")

    def test_unknown_material(self):
        self.assertIsNone(parse_recycle_material("rubber"))


class TestSuggestionGeneration(unittest.TestCase):
    """Personalised suggestions based on total emission."""

    def test_high_emission_warning(self):
        suggestions = generate_personalised_suggestions(25.0)
        combined = " ".join(suggestions)
        self.assertIn("high", combined.lower())

    def test_medium_emission_warning(self):
        suggestions = generate_personalised_suggestions(15.0)
        combined = " ".join(suggestions)
        self.assertIn("above average", combined.lower())

    def test_low_emission_praise(self):
        suggestions = generate_personalised_suggestions(3.0)
        combined = " ".join(suggestions)
        self.assertIn("great", combined.lower())

    def test_returns_list(self):
        self.assertIsInstance(generate_personalised_suggestions(0), list)


class TestGetTips(unittest.TestCase):
    """Tip retrieval."""

    def test_returns_correct_count(self):
        self.assertEqual(len(get_tips(3)), 3)

    def test_minimum_one_tip(self):
        self.assertGreaterEqual(len(get_tips(0)), 1)

    def test_tips_are_strings(self):
        for tip in get_tips(5):
            self.assertIsInstance(tip, str)


class TestBuildSummary(unittest.TestCase):
    """Summary formatting."""

    def test_empty_activities_message(self):
        result = build_summary([], 0.0)
        self.assertIn("No activities", result)

    def test_summary_contains_total(self):
        activities = [{"type": "travel", "detail": "10 km", "emission": 2.1}]
        result = build_summary(activities, 2.1)
        self.assertIn("2.10", result)

    def test_summary_lists_activity_type(self):
        activities = [{"type": "electricity", "detail": "5 units", "emission": 4.1}]
        result = build_summary(activities, 4.1)
        self.assertIn("Electricity", result)


class TestFormatEmission(unittest.TestCase):
    """Emission string formatting."""

    def test_two_decimal_places(self):
        self.assertEqual(format_emission(2.1), "2.10 kg CO₂")

    def test_zero(self):
        self.assertEqual(format_emission(0.0), "0.00 kg CO₂")


# ── assistant.py tests ────────────────────────────────────────────────────────

class TestIntentDetection(unittest.TestCase):
    """CarbonAssistant._detect_intent coverage."""

    def test_travel_intent(self):
        self.assertEqual(CarbonAssistant._detect_intent("travel 20 km"), "travel")

    def test_electricity_intent(self):
        self.assertEqual(CarbonAssistant._detect_intent("electricity 10 units"), "electricity")

    def test_meals_intent(self):
        self.assertEqual(CarbonAssistant._detect_intent("meals 3 vegetarian"), "meals")

    def test_recycle_intent(self):
        self.assertEqual(CarbonAssistant._detect_intent("recycle plastic"), "recycle")

    def test_summary_intent(self):
        self.assertEqual(CarbonAssistant._detect_intent("summary"), "summary")

    def test_tips_intent(self):
        self.assertEqual(CarbonAssistant._detect_intent("tips"), "tips")

    def test_history_intent(self):
        self.assertEqual(CarbonAssistant._detect_intent("history"), "history")

    def test_unknown_intent(self):
        self.assertEqual(CarbonAssistant._detect_intent("blah blah"), "unknown")

    def test_case_insensitive(self):
        self.assertEqual(CarbonAssistant._detect_intent("TRAVEL 5 KM"), "travel")


class TestAssistantTravelCommand(unittest.TestCase):
    """process() → travel handler."""

    def setUp(self):
        self.assistant = CarbonAssistant()

    def test_valid_travel(self):
        response = self.assistant.process("travel 20 km")
        self.assertIn("20", response)
        self.assertIn("4.20", response)     # 20 × 0.21

    def test_travel_updates_total(self):
        self.assistant.process("travel 10 km")
        self.assertAlmostEqual(self.assistant.get_total_emission(), 2.1, places=4)

    def test_invalid_travel_no_number(self):
        response = self.assistant.process("travel km")
        self.assertIn("⚠️", response)

    def test_travel_negative_ignored(self):
        # Negative distance should produce an error, not a negative emission
        response = self.assistant.process("travel -5 km")
        self.assertIn("⚠️", response)


class TestAssistantElectricityCommand(unittest.TestCase):
    """process() → electricity handler."""

    def setUp(self):
        self.assistant = CarbonAssistant()

    def test_valid_electricity(self):
        response = self.assistant.process("electricity 10 units")
        self.assertIn("8.20", response)     # 10 × 0.82

    def test_electricity_updates_total(self):
        self.assistant.process("electricity 5 units")
        self.assertAlmostEqual(self.assistant.get_total_emission(), 4.1, places=4)

    def test_invalid_electricity(self):
        response = self.assistant.process("electricity units")
        self.assertIn("⚠️", response)


class TestAssistantMealsCommand(unittest.TestCase):
    """process() → meals handler."""

    def setUp(self):
        self.assistant = CarbonAssistant()

    def test_vegetarian_meals(self):
        response = self.assistant.process("meals 3 vegetarian")
        self.assertIn("3.00", response)

    def test_nonveg_meals(self):
        response = self.assistant.process("meals 2 nonveg")
        self.assertIn("6.00", response)     # 2 × 3.0

    def test_invalid_meals_no_type(self):
        response = self.assistant.process("meals 3")
        self.assertIn("⚠️", response)

    def test_invalid_meals_no_count(self):
        response = self.assistant.process("meals vegetarian")
        self.assertIn("⚠️", response)


class TestAssistantRecycleCommand(unittest.TestCase):
    """process() → recycle handler."""

    def setUp(self):
        self.assistant = CarbonAssistant()

    def test_recycle_reduces_total(self):
        self.assistant.process("travel 10 km")          # +2.1
        self.assistant.process("recycle plastic")        # -0.5
        self.assertAlmostEqual(self.assistant.get_total_emission(), 1.6, places=4)

    def test_recycle_response_mentions_material(self):
        response = self.assistant.process("recycle paper")
        self.assertIn("paper", response.lower())

    def test_invalid_recycle_material(self):
        response = self.assistant.process("recycle rubber")
        self.assertIn("⚠️", response)

    def test_recycle_no_material(self):
        response = self.assistant.process("recycle")
        self.assertIn("⚠️", response)


class TestAssistantSummary(unittest.TestCase):
    """process('summary') output."""

    def setUp(self):
        self.assistant = CarbonAssistant()

    def test_empty_summary(self):
        response = self.assistant.process("summary")
        self.assertIn("No activities", response)

    def test_summary_after_activity(self):
        self.assistant.process("travel 50 km")
        response = self.assistant.process("summary")
        self.assertIn("Travel", response)
        self.assertIn("10.50", response)    # 50 × 0.21

    def test_summary_contains_suggestions(self):
        response = self.assistant.process("summary")
        # Should always include at least one emoji from suggestions
        self.assertTrue(any(c in response for c in ("🟢", "🟡", "🔴")))


class TestAssistantHistory(unittest.TestCase):
    """process('history') output."""

    def setUp(self):
        self.assistant = CarbonAssistant()

    def test_empty_history(self):
        response = self.assistant.process("history")
        self.assertIn("No activities", response)

    def test_history_lists_entries(self):
        self.assistant.process("travel 10 km")
        self.assistant.process("meals 2 vegetarian")
        response = self.assistant.process("history")
        self.assertIn("travel", response.lower())
        self.assertIn("meals", response.lower())

    def test_history_count(self):
        self.assistant.process("electricity 5 units")
        self.assistant.process("recycle glass")
        activities = self.assistant.get_activities()
        self.assertEqual(len(activities), 2)


class TestAssistantSessionMemory(unittest.TestCase):
    """Running total accumulates correctly across commands."""

    def setUp(self):
        self.assistant = CarbonAssistant()

    def test_total_accumulates(self):
        self.assistant.process("travel 10 km")          # 2.1
        self.assistant.process("electricity 5 units")   # 4.1
        self.assertAlmostEqual(self.assistant.get_total_emission(), 6.2, places=4)

    def test_recycle_offsets_total(self):
        self.assistant.process("meals 1 nonveg")         # 3.0
        self.assistant.process("recycle plastic")         # -0.5
        self.assertAlmostEqual(self.assistant.get_total_emission(), 2.5, places=4)

    def test_multiple_sessions_are_independent(self):
        a = CarbonAssistant()
        b = CarbonAssistant()
        a.process("travel 100 km")
        self.assertEqual(b.get_total_emission(), 0.0)


class TestAssistantEdgeCases(unittest.TestCase):
    """Empty input, very long input, and garbage commands."""

    def setUp(self):
        self.assistant = CarbonAssistant()

    def test_empty_input(self):
        response = self.assistant.process("")
        self.assertIn("didn't catch", response.lower())

    def test_whitespace_only_input(self):
        response = self.assistant.process("   ")
        self.assertIn("didn't catch", response.lower())

    def test_too_long_input(self):
        long_input = "x" * (MAX_INPUT_LENGTH + 10)
        response = self.assistant.process(long_input)
        self.assertIn("too long", response.lower())

    def test_unknown_command(self):
        response = self.assistant.process("fly to the moon")
        self.assertIn("didn't recognise", response.lower())

    def test_tips_command(self):
        response = self.assistant.process("tips")
        self.assertIn("Tip", response)

    def test_numeric_only_input(self):
        response = self.assistant.process("42")
        self.assertIn("didn't recognise", response.lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)