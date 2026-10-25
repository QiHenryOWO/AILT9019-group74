import os
import unittest
from unittest.mock import Mock, patch

with patch.dict(os.environ, {"BAILIAN_API_KEY": "test-key"}):
    from src import pipeline


class TestPipeline(unittest.TestCase):

    @staticmethod
    def _response(text):
        response = Mock()
        response.choices = [Mock()]
        response.choices[0].message.content = text
        return response

    def test_refusal_short_circuits_retrieval_and_api(self):
        with patch(
            "src.pipeline.refusal_mod.check_refusal",
            return_value=(True, ["medical"]),
        ) as check_refusal, patch(
            "src.pipeline.index_mod.load_index"
        ) as load_index, patch(
            "src.pipeline.retrieve"
        ) as retrieve, patch(
            "src.pipeline.get_client"
        ) as get_client:
            result = pipeline.answer("What medicine should I take?")

        self.assertTrue(result["refused"])
        self.assertEqual(result["answer"], pipeline.refusal_mod.HOTLINE)
        self.assertEqual(result["sources"], [])
        self.assertEqual(result["categories"], ["medical"])
        check_refusal.assert_called_once_with("What medicine should I take?")
        load_index.assert_not_called()
        retrieve.assert_not_called()
        get_client.assert_not_called()

    def test_rag_path_builds_context_and_returns_sources(self):
        docs = [
            {
                "title": "Library Study Rooms",
                "url": "https://example.com/library",
                "text": "Book a group study room online.",
            },
            {
                "title": "CEDARS",
                "url": "https://example.com/cedars",
                "text": "Financial support for students.",
            },
        ]
        client = Mock()
        client.chat.completions.create.return_value = self._response(
            "Grounded answer."
        )

        with patch(
            "src.pipeline.refusal_mod.check_refusal",
            return_value=(False, []),
        ) as check_refusal, patch(
            "src.pipeline.index_mod.load_index",
            return_value={"docs": docs},
        ) as load_index, patch(
            "src.pipeline.retrieve",
            return_value=docs,
        ) as retrieve, patch(
            "src.pipeline.get_client",
            return_value=client,
        ):
            result = pipeline.answer("How do I book a room?")

        self.assertFalse(result["refused"])
        self.assertEqual(result["answer"], "Grounded answer.")
        self.assertEqual(
            result["sources"],
            [
                {
                    "title": "Library Study Rooms",
                    "url": "https://example.com/library",
                },
                {"title": "CEDARS", "url": "https://example.com/cedars"},
            ],
        )
        check_refusal.assert_called_once_with("How do I book a room?")
        load_index.assert_called_once_with()
        retrieve.assert_called_once()
        self.assertEqual(retrieve.call_args.args[0], "How do I book a room?")
        self.assertEqual(retrieve.call_args.args[1], {"docs": docs})
        self.assertEqual(retrieve.call_args.kwargs, {"top_k": 3})

        create = client.chat.completions.create
        create.assert_called_once()
        request = create.call_args.kwargs
        self.assertEqual(request["model"], pipeline.config.CHAT_MODEL)
        self.assertEqual(request["temperature"], 0.2)
        self.assertEqual(request["max_tokens"], 400)
        self.assertEqual(
            request["messages"][0],
            {"role": "system", "content": pipeline.SYSTEM_PROMPT},
        )
        self.assertEqual(request["messages"][1]["role"], "user")
        user_message = request["messages"][1]["content"]
        self.assertIn("Library Study Rooms", user_message)
        self.assertIn("https://example.com/library", user_message)
        self.assertIn("Book a group study room online.", user_message)
        self.assertIn("How do I book a room?", user_message)

    def test_no_results_uses_fallback_context(self):
        client = Mock()
        client.chat.completions.create.return_value = self._response(
            "I do not have that information."
        )

        with patch(
            "src.pipeline.refusal_mod.check_refusal",
            return_value=(False, []),
        ), patch(
            "src.pipeline.index_mod.load_index",
            return_value={"docs": []},
        ), patch(
            "src.pipeline.retrieve",
            return_value=[],
        ), patch(
            "src.pipeline.get_client",
            return_value=client,
        ):
            result = pipeline.answer("Where is the cafeteria?")

        self.assertFalse(result["refused"])
        self.assertEqual(result["answer"], "I do not have that information.")
        self.assertEqual(result["sources"], [])
        request = client.chat.completions.create.call_args.kwargs
        self.assertIn(
            "(No relevant HKU service information was found in the index.)",
            request["messages"][1]["content"],
        )


if __name__ == "__main__":
    unittest.main()
