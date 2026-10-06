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
    first_pass_reviewer: str = "opus"
    reviewer_models: dict[str, str] = {"opus": "Claude Opus 5.5", "sonnet": "Claude Sonnet 5.5", "fable": "Claude Fable 5.1"}
    reviews_dir: Path = RAW_DIR / "review" / "reviews"
    consensus: Path = RAW_DIR / "review" / "consensus.jsonl"
    adjudication_packet: Path = RAW_DIR / "review" / "adjudication_packet.jsonl"
    adjudications_dir: Path = RAW_DIR / "review" / "adjudications"
    question_rewrites: Path = RAW_DIR / "review" / "question_rewrites.jsonl"
    dataset_dir: Path = TRACK_DIR / "data" / "dataset"
    dataset_license: str = "CDLA-Permissive-2.0"
    eval_config: Path = TRACK_DIR / "data" / "eval.yaml"
    grader_prompt: Path = TRACK_DIR / "data" / "grader" / "simpleqa_grader.txt"
    # Evaluation calls contain only our own questions and the models' replies, so they are published.
    recordings_dir: Path = TRACK_DIR / "data" / "recordings"
    responses: Path = TRACK_DIR / "data" / "dataset" / "responses.jsonl"
    results_dir: Path = TRACK_DIR / "results"
    # The challenge asks for a human check of a random 20% of the judge's grades.
    human_sample_share: float = 0.2
    human_sample_seed: int = 20261016
    human_page_template: Path = Path(__file__).parent / "human_page.html"
    human_page: Path = TRACK_DIR / "data" / "human" / "judge_check.html"
    # One file per grader (key, grade): the primary grader of every response, graders of the blind sample.
    grades_dir: Path = TRACK_DIR / "data" / "grades"
    card_template: Path = TRACK_DIR / "docs" / "dataset_card.template.md"
    card: Path = TRACK_DIR / "docs" / "dataset_card.md"
    # Folder uploaded to the Hugging Face dataset repository; rebuilt by `make hf`, not committed.
    hf_dir: Path = TRACK_DIR / "hf"
    source_publisher: str = "ch.ch, Swiss Federal Chancellery (source of facts only; no text reproduced)"
    max_copied_words: int = 8
    # Languages the reviewer does not read: the review sheet adds an English translation for these.
    translate_for_review: list[str] = ["de", "it"]
    # ch.ch answers 404 to the default httpx and curl User-Agents.
    user_agent: str = "Mozilla/5.0 (compatible; LargeCaneleModel/0.1)"
    fetch_timeout_s: float = 30.0
    fetch_delay_s: float = 1.0
