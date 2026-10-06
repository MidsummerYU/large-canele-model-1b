from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

TRACK_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = TRACK_DIR / "data" / "raw"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=TRACK_DIR / ".env", extra="ignore")

    llm_base_url: str = ""
    llm_api_key: SecretStr = SecretStr("")
    llm_timeout_s: float = 300.0
    llm_max_retries: int = 8
    concurrency: int = 4

    generator_model: str = "swiss-ai/Apertus-v1.5-70B"
    generator_temperature: float = 0.0
    generator_max_tokens: int = 2048
    passages_per_question: int = 3
    max_questions_per_page: int = 10

    sources: Path = TRACK_DIR / "data" / "sources.yaml"
    raw_dir: Path = RAW_DIR / "chch"
    # Generation prompts contain ch.ch text, so their recordings stay unpublished like the pages.
    generation_recordings_dir: Path = RAW_DIR / "recordings"
    candidates: Path = RAW_DIR / "candidates.jsonl"
    review_sheet: Path = RAW_DIR / "review" / "candidates.csv"
    # First-pass suggestions by an AI reviewer; the human decision columns stay separate.
    review_suggestions: Path = RAW_DIR / "review" / "suggestions.jsonl"
    # Languages the reviewer does not read: the review sheet adds an English translation for these.
    translate_for_review: list[str] = ["de", "it"]
    # ch.ch answers 404 to the default httpx and curl User-Agents.
    user_agent: str = "Mozilla/5.0 (compatible; LargeCaneleModel/0.1)"
    fetch_timeout_s: float = 30.0
    fetch_delay_s: float = 1.0
