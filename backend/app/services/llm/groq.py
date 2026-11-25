import groq
from collections.abc import Iterator

from app.services.llm.base import LLMProvider, ProviderError


class GroqProvider(LLMProvider):
    def __init__(self, api_key: str):
        if not api_key:
            raise ProviderError("Groq is not configured. Add GROQ_API_KEY to backend/.env.", 503)
        self.client = groq.Groq(api_key=api_key, timeout=30.0, max_retries=0)

    def generate(self, system: str, prompt: str, model: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
                temperature=0.1,
            )
            text = response.choices[0].message.content
            if not text:
                raise ProviderError("Groq returned no answer. Try a different question.")
            return text
        except groq.AuthenticationError as exc:
            raise ProviderError("Groq credentials are invalid. Check GROQ_API_KEY.", 503) from exc
        except groq.RateLimitError as exc:
            raise ProviderError("Groq rate limit was reached. Wait and retry.", 429) from exc
        except groq.NotFoundError as exc:
            raise ProviderError("The configured Groq model is unavailable. Check GROQ_MODEL in Settings.", 503) from exc
        except groq.APITimeoutError as exc:
            raise ProviderError("Groq timed out. Please try again.", 504) from exc
        except groq.APIError as exc:
            raise ProviderError("Groq could not complete the request. Please try again.") from exc

    def stream(self, system: str, prompt: str, model: str) -> Iterator[str]:
        try:
            stream = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
                temperature=0.1, stream=True,
            )
            for part in stream:
                if part.choices and part.choices[0].delta.content:
                    yield part.choices[0].delta.content
        except groq.RateLimitError as exc:
            raise ProviderError("Groq rate limit was reached. Wait and retry.", 429) from exc
        except groq.AuthenticationError as exc:
            raise ProviderError("Groq credentials are invalid.", 503) from exc
        except groq.NotFoundError as exc:
            raise ProviderError("The configured Groq model is unavailable.", 503) from exc
        except groq.APITimeoutError as exc:
            raise ProviderError("Groq timed out.", 504) from exc
        except groq.APIError as exc:
            raise ProviderError("Groq streaming failed.") from exc
