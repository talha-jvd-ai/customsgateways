from openai import OpenAI
from typing import List
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings

settings = get_settings()
client = OpenAI(api_key=settings.openai_api_key)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def generate_embedding(text: str) -> List[float]:
    """Generate embedding vector using OpenAI."""
    response = client.embeddings.create(
        model=settings.embedding_model,
        input=text,
        encoding_format="float"
    )
    return response.data[0].embedding


def prepare_text_for_embedding(description: str, country: str) -> str:
    """Combine description and country for embedding."""
    return f"{description} origin {country}"


def test_openai_connection() -> bool:
    try:
        generate_embedding("test")
        return True
    except Exception as e:
        print(f"OpenAI connection failed: {e}")
        return False
