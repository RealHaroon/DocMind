from google import genai
from google.genai import errors, types
from collections.abc import Iterator

from app.services.llm.base import LLMProvider, ProviderError


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str):
        if not api_key:
            raise ProviderError("Gemini is not configured. Add GEMINI_API_KEY to backend/.env.", 503)
        self.client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=30000))

    def generate(self, system: str, prompt: str, model: str) -> str:
        try:
            response = self.client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(system_instruction=system, temperature=0.1),
            )
            if not response.text:
                raise ProviderError("Gemini returned no answer. Try a different question.")
            return response.text
        except errors.APIError as exc:
            if exc.code in (401, 403):
                raise ProviderError("Gemini credentials are invalid or this model is unavailable to your account.", 503) from exc
            if exc.code == 429:
                raise ProviderError("Gemini quota was reached. Wait or choose Groq explicitly in Settings.", 429) from exc
            if exc.code == 404:
                raise ProviderError("The configured Gemini model is unavailable. Check GEMINI_MODEL in Settings.", 503) from exc
            raise ProviderError("Gemini could not complete the request. Please try again.") from exc
        except TimeoutError as exc:
            raise ProviderError("Gemini timed out. Please try again.", 504) from exc

    def stream(self, system: str, prompt: str, model: str) -> Iterator[str]:
        try:
            for part in self.client.models.generate_content_stream(
                model=model, contents=prompt,
                config=types.GenerateContentConfig(system_instruction=system, temperature=0.1),
            ):
                if part.text:
                    yield part.text
        except errors.APIError as exc:
            if exc.code == 429:
                raise ProviderError("Gemini quota was reached. Wait and retry.", 429) from exc
            if exc.code in (401, 403, 404):
                raise ProviderError("Gemini credentials or configured model are unavailable.", 503) from exc
            raise ProviderError("Gemini streaming failed.") from exc
        except TimeoutError as exc:
            raise ProviderError("Gemini timed out.", 504) from exc
