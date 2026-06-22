import json
import logging
import requests
from django.conf import settings
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

class LLMService:
    OLLAMA_URL = getattr(settings, "OLLAMA_URL", "http://localhost:11434/api/generate")
    OLLAMA_MODEL = getattr(settings, "OLLAMA_MODEL", "llama3")
    GEMINI_API_KEY = getattr(settings, "GEMINI_API_KEY", "")

    @classmethod
    def _query_ollama(cls, system_prompt: str, user_prompt: str, expect_json: bool = False) -> str:
        try:
            full_prompt = f"System: {system_prompt}\n\nUser: {user_prompt}"
            payload = {
                "model": cls.OLLAMA_MODEL,
                "prompt": full_prompt,
                "stream": False,
            }
            if expect_json:
                payload["format"] = "json"
                
            response = requests.post(cls.OLLAMA_URL, json=payload, timeout=25.0)
            if response.status_code == 200:
                return response.json().get("response", "")
        except Exception as e:
            logger.warning(f"Ollama query failed: {e}")
        return None

    @classmethod
    def _query_gemini(cls, system_prompt: str, user_prompt: str, expect_json: bool = False) -> str:
        if not cls.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not configured in settings.")
        
        try:
            client = genai.Client(api_key=cls.GEMINI_API_KEY)
            config = types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.2,
            )
            if expect_json:
                config.response_mime_type = "application/json"

            response = client.models.generate_content(
                model='gemini-1.5-flash',
                contents=user_prompt,
                config=config
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini API query failed: {e}")
            raise e

    @classmethod
    def query(cls, system_prompt: str, user_prompt: str, expect_json: bool = False) -> str:
        # 1. Try local Ollama first
        result = cls._query_ollama(system_prompt, user_prompt, expect_json)
        if result:
            return result
        
        # 2. Fall back to Gemini API
        logger.info("Falling back to Gemini 1.5 Flash API...")
        return cls._query_gemini(system_prompt, user_prompt, expect_json)

    @classmethod
    def generate_itinerary(cls, destination: str, days_count: int, start_date: str, details: str = "") -> dict:
        system_prompt = (
            "You are an expert travel planner. You create comprehensive, highly engaging, family-friendly itineraries.\n"
            "You must output ONLY a valid JSON object matching the following structure:\n"
            "{\n"
            "  \"title\": \"String (e.g. Lisbon Family Adventure 2026)\",\n"
            "  \"currency\": \"String (e.g. EUR)\",\n"
            "  \"conversion_rate\": 1.10, // Float, conversion rate from 1 USD to local currency\n"
            "  \"days\": [\n"
            "    {\n"
            "      \"day_number\": 1, // Integer\n"
            "      \"theme\": \"String (e.g. Arrival & The Green Bazaar)\",\n"
            "      \"early_start_banner\": \"String (optional, e.g. Early Start at 7:00 AM)\",\n"
            "      \"stops\": [\n"
            "        {\n"
            "          \"sequence_order\": 1, // Integer\n"
            "          \"time_label\": \"String (e.g. Noon — Settle in)\",\n"
            "          \"title\": \"String (e.g. Airbnb Check-In)\",\n"
            "          \"description\": \"String (Detailed description of the stop and notes for families)\",\n"
            "          \"latitude\": 40.3777, // Float (must be accurate geocoordinates for the destination)\n"
            "          \"longitude\": 49.8467, // Float\n"
            "          \"zoom_level\": 15, // Integer\n"
            "          \"cost_local\": 10.00, // Decimal cost in local currency\n"
            "          \"cost_usd\": 6.00, // Decimal cost in USD\n"
            "          \"meal_type\": \"String (optional: Breakfast, Lunch, Dinner, Snack)\",\n"
            "          \"meal_name\": \"String (optional)\",\n"
            "          \"meal_desc\": \"String (optional)\",\n"
            "          \"meal_price_label\": \"String (optional, e.g. ~20 AZN / $12)\",\n"
            "          \"meal_recommendation\": \"String (optional, e.g. For toddler: request plain chicken)\",\n"
            "          \"tags\": [\"Tag1\", \"Tag2\"], // Array of short tags (e.g. 'Near metro', 'Kid-friendly')\n"
            "          \"color_hex\": \"String (hex color e.g. #27AE60)\"\n"
            "        }\n"
            "      ]\n"
            "    }\n"
            "  ]\n"
            "}"
        )
        
        user_prompt = (
            f"Generate a {days_count}-day itinerary for '{destination}' starting on '{start_date}'.\n"
            f"Additional guidelines: {details}\n"
            f"Make sure to provide real and accurate geocoordinates (latitude and longitude) for all stops in {destination}.\n"
            f"Include distinct details for local breakfasts, dinners, family notes, and toddler tips."
        )

        raw_response = cls.query(system_prompt, user_prompt, expect_json=True)
        try:
            return json.loads(raw_response)
        except Exception as e:
            logger.error(f"Failed to parse AI itinerary response: {e}. Raw response: {raw_response}")
            # Try parsing if markdown blocks are included
            if "```json" in raw_response:
                try:
                    cleaned = raw_response.split("```json")[1].split("```")[0].strip()
                    return json.loads(cleaned)
                except Exception:
                    pass
            raise e

    @classmethod
    def edit_agenda(cls, current_day_data: dict, command: str) -> list:
        system_prompt = (
            "You are an itinerary database mutation agent. The user will ask to modify a specific day's list of stops.\n"
            "You will receive the current day's stops as a JSON list, and the user's request.\n"
            "You must outputs ONLY a valid JSON list of database actions to perform.\n"
            "Supported actions are 'CREATE', 'UPDATE', or 'DELETE'.\n"
            "Output format must be a list of action objects:\n"
            "[\n"
            "  {\n"
            "    \"action\": \"UPDATE|CREATE|DELETE\",\n"
            "    \"stop_id\": 123, // Integer (null for CREATE)\n"
            "    \"fields\": { // Object containing fields to set/update. Leave out fields that did not change.\n"
            "      \"sequence_order\": 1,\n"
            "      \"time_label\": \"3:00 PM\",\n"
            "      \"title\": \"Updated Stop Title\",\n"
            "      \"description\": \"Updated description\",\n"
            "      \"latitude\": 40.3700,\n"
            "      \"longitude\": 49.8300,\n"
            "      \"zoom_level\": 15,\n"
            "      \"cost_local\": 25.00,\n"
            "      \"cost_usd\": 15.00,\n"
            "      \"meal_type\": \"Lunch\",\n"
            "      \"meal_name\": \"Kebab House\",\n"
            "      \"meal_desc\": \"...\","
            "      \"tags\": [\"Tag1\"],\n"
            "      \"color_hex\": \"#E67E22\"\n"
            "    }\n"
            "  }\n"
            "]\n"
            "CRITICAL: If stops are reordered, created, or deleted, you MUST generate UPDATE actions for all affected stops "
            "to ensure their 'sequence_order' is sequential (1, 2, 3...) and matches the new chronological flow.\n"
            "For CREATE actions, generate realistic coordinates, descriptions, and details for the requested stop."
        )

        user_prompt = (
            f"Current Day Stops JSON:\n{json.dumps(current_day_data, indent=2)}\n\n"
            f"User request: {command}"
        )

        raw_response = cls.query(system_prompt, user_prompt, expect_json=True)
        try:
            return json.loads(raw_response)
        except Exception as e:
            logger.error(f"Failed to parse AI edit mutation response: {e}. Raw: {raw_response}")
            if "```json" in raw_response:
                try:
                    cleaned = raw_response.split("```json")[1].split("```")[0].strip()
                    return json.loads(cleaned)
                except Exception:
                    pass
            raise e

    @classmethod
    def parse_booking(cls, text_content: str) -> dict:
        system_prompt = (
            "You are a booking confirmation parser. Extract booking details from the text content provided.\n"
            "You must output ONLY a valid JSON object matching the following structure:\n"
            "{\n"
            "  \"booking_type\": \"Flight|Hotel|Activity|Restaurant\",\n"
            "  \"title\": \"String (e.g. Hotel check-in or Flight details)\",\n"
            "  \"confirmation_number\": \"String (optional)\",\n"
            "  \"details\": \"String (Key summary of timing, dates, address, flight numbers)\",\n"
            "  \"start_time\": \"ISO-8601 String or null (YYYY-MM-DDTHH:MM:SS)\",\n"
            "  \"end_time\": \"ISO-8601 String or null (YYYY-MM-DDTHH:MM:SS)\",\n"
            "  \"cost\": 120.00 // Float or null (in USD)\n"
            "}"
        )

        raw_response = cls.query(system_prompt, text_content, expect_json=True)
        try:
            return json.loads(raw_response)
        except Exception as e:
            logger.error(f"Failed to parse booking: {e}. Raw: {raw_response}")
            if "```json" in raw_response:
                try:
                    cleaned = raw_response.split("```json")[1].split("```")[0].strip()
                    return json.loads(cleaned)
                except Exception:
                    pass
            raise e
