import json
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings

from itinerary.services.llm import LLMService


class LLMJsonParsingTestCase(SimpleTestCase):
    @patch.object(LLMService, "query", return_value='{"title": "Trip", "currency": "USD", "conversion_rate": 1.0, "days": []}')
    def test_generate_itinerary_parses_plain_json(self, _mock_query):
        result = LLMService.generate_itinerary("Lisbon", 1, "2026-07-01")
        self.assertEqual(result["title"], "Trip")
        self.assertEqual(result["currency"], "USD")

    @patch.object(
        LLMService,
        "query",
        return_value='```json\n{"title": "Fenced", "currency": "EUR", "conversion_rate": 1.1, "days": []}\n```',
    )
    def test_generate_itinerary_strips_markdown_fence(self, _mock_query):
        result = LLMService.generate_itinerary("Paris", 2, "2026-08-01")
        self.assertEqual(result["title"], "Fenced")

    @patch.object(LLMService, "query", return_value="not valid json")
    def test_generate_itinerary_raises_on_invalid_json(self, _mock_query):
        with self.assertRaises(json.JSONDecodeError):
            LLMService.generate_itinerary("Rome", 1, "2026-07-01")

    @patch.object(LLMService, "query", return_value='[{"action": "DELETE", "stop_id": 5}]')
    def test_edit_agenda_parses_mutation_list(self, _mock_query):
        result = LLMService.edit_agenda([], "remove stop 5")
        self.assertEqual(result[0]["action"], "DELETE")
        self.assertEqual(result[0]["stop_id"], 5)

    @patch.object(
        LLMService,
        "query",
        return_value='```json\n[{"action": "UPDATE", "stop_id": 1, "fields": {"title": "New"}}]\n```',
    )
    def test_edit_agenda_strips_markdown_fence(self, _mock_query):
        result = LLMService.edit_agenda([{"id": 1}], "rename")
        self.assertEqual(result[0]["fields"]["title"], "New")

    @patch.object(
        LLMService,
        "query",
        return_value='{"booking_type": "Hotel", "title": "Stay", "confirmation_number": "X1", "details": "Check-in 3pm", "cost": 90}',
    )
    def test_parse_booking_parses_json(self, _mock_query):
        result = LLMService.parse_booking("Hotel booking X1")
        self.assertEqual(result["booking_type"], "Hotel")
        self.assertEqual(result["confirmation_number"], "X1")

    @patch.object(
        LLMService,
        "query",
        return_value='```json\n{"booking_type": "Flight", "title": "TK337", "confirmation_number": "G8J2X4", "details": "IST-Baku", "cost": 350}\n```',
    )
    def test_parse_booking_strips_markdown_fence(self, _mock_query):
        result = LLMService.parse_booking("paste")
        self.assertEqual(result["title"], "TK337")

    @patch.object(LLMService, "query", return_value="{broken")
    def test_parse_booking_raises_on_invalid_json(self, _mock_query):
        with self.assertRaises(json.JSONDecodeError):
            LLMService.parse_booking("broken")


class LLMQueryRoutingTestCase(SimpleTestCase):
    @patch.object(LLMService, "_query_gemini")
    @patch.object(LLMService, "_query_ollama", return_value="ollama-response")
    def test_query_uses_ollama_when_available(self, _mock_ollama, mock_gemini):
        result = LLMService.query("system", "user")
        self.assertEqual(result, "ollama-response")
        mock_gemini.assert_not_called()

    @patch.object(LLMService, "_query_gemini", return_value="gemini-response")
    @patch.object(LLMService, "_query_ollama", return_value=None)
    def test_query_falls_back_to_gemini(self, _mock_ollama, _mock_gemini):
        result = LLMService.query("system", "user")
        self.assertEqual(result, "gemini-response")

    @override_settings(GEMINI_API_KEY="")
    def test_gemini_requires_api_key(self):
        with self.assertRaises(ValueError):
            LLMService._query_gemini("system", "user")

    @patch("itinerary.services.llm.requests.post")
    def test_ollama_returns_response_text_on_success(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200, json=lambda: {"response": "hello"})
        result = LLMService._query_ollama("system", "user")
        self.assertEqual(result, "hello")

    @patch("itinerary.services.llm.requests.post", side_effect=ConnectionError("down"))
    def test_ollama_returns_none_on_failure(self, _mock_post):
        result = LLMService._query_ollama("system", "user")
        self.assertIsNone(result)
