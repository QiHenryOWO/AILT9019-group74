
import unittest

from src.refusal import HOTLINE, check_refusal


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
        
    def test_uppercase_query_is_refused(self):
        refused, categories = check_refusal("I HAVE CHEST PAIN")

        self.assertTrue(refused)
        self.assertIn("medical", categories)

    def test_multiple_categories_are_reported(self):
        refused, categories = check_refusal(
            "I have chest pain and want to sue my landlord"
        )

        self.assertTrue(refused)
        self.assertIn("medical", categories)
        self.assertIn("legal", categories)
        
    def test_medical_library_is_not_refused(self):
        refused, categories = check_refusal("Where is the medical library?")

        self.assertFalse(refused)
        self.assertEqual(categories, [])

    def test_legal_studies_question_is_not_refused(self):
        refused, categories = check_refusal(
            "What courses are in the legal studies programme?"
        )

        self.assertFalse(refused)
        self.assertEqual(categories, [])

    def test_hotline_contains_official_contacts(self):
        self.assertIn("999", HOTLINE)
        self.assertIn("UHS", HOTLINE)
        self.assertIn("2389 2222", HOTLINE)


if __name__ == "__main__":
    unittest.main()
