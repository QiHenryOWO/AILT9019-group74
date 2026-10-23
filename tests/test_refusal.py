
import unittest

from src.refusal import check_refusal


class TestRefusal(unittest.TestCase):

    def test_medical_question_triggers_refusal(self):
        refused, categories = check_refusal(
            "What medication should I take for my fever?"
        )

        self.assertTrue(refused)
        self.assertIn("medical", categories)

    def test_mental_health_question_triggers_refusal(self):
        refused, categories = check_refusal(
            "I am feeling depressed"
        )

        self.assertTrue(refused)
        self.assertIn("mental_health", categories)

    def test_legal_question_triggers_refusal(self):
        refused, categories = check_refusal(
            "Can I sue my landlord?"
        )

        self.assertTrue(refused)
        self.assertIn("legal", categories)

    def test_emergency_question_triggers_refusal(self):
        refused, categories = check_refusal(
            "Someone is unconscious"
        )

        self.assertTrue(refused)
        self.assertIn("emergency", categories)

    def test_university_service_question_is_not_refused(self):
        refused, categories = check_refusal(
            "What services does UHS offer?"
        )

        self.assertFalse(refused)
        self.assertEqual(categories, [])

    def test_emergency_loan_is_not_refused(self):
        refused, categories = check_refusal(
            "How can I apply for an emergency loan?"
        )

        self.assertFalse(refused)
        self.assertEqual(categories, [])

    def test_empty_query_is_not_refused(self):
        refused, categories = check_refusal("")

        self.assertFalse(refused)
        self.assertEqual(categories, [])


if __name__ == "__main__":
    unittest.main()
