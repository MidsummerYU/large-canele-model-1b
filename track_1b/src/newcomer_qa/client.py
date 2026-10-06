import hashlib
import threading
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from openai import OpenAI
from pydantic import BaseModel, ConfigDict

from newcomer_qa.config import Settings

Mode = Literal["live", "replay"]


class MissingRecordingError(LookupError):
    pass


class ChatRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    model: str
    messages: tuple[tuple[str, str], ...]
    temperature: float
    max_tokens: int

    def key(self) -> str:
        return hashlib.sha256(self.model_dump_json().encode()).hexdigest()


class Recording(BaseModel):
    key: str
    request: ChatRequest
    content: str
    served_model: str | None
    usage: dict[str, int] | None
    endpoint: str
    latency_ms: int
    recorded_at: datetime


class RecordingClient:
    def __init__(self, settings: Settings, recordings_dir: Path, mode: Mode, api: OpenAI | None = None):
        self._base_url = settings.llm_base_url
        # One file per endpoint and model: providers spell model ids with different casing,
        # which collides on case-insensitive filesystems (macOS).
        self._dir = recordings_dir / (urlparse(settings.llm_base_url).hostname or "unknown-endpoint")
        self._mode = mode
        self._lock = threading.Lock()
        self._recordings = self._load()
        self._api = api if api is not None or mode == "replay" else OpenAI(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key.get_secret_value(),
            timeout=settings.llm_timeout_s,
            max_retries=settings.llm_max_retries,
        )

    def _path(self, model: str) -> Path:
        return self._dir / f"{model.replace('/', '__')}.jsonl"

    def _load(self) -> dict[str, Recording]:
        recordings = {}
        for path in sorted(self._dir.glob("*.jsonl")):
            with path.open(encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        recording = Recording.model_validate_json(line)
                        recordings[recording.key] = recording
        return recordings

    def chat(self, request: ChatRequest) -> Recording:
        key = request.key()
        if key in self._recordings:
            return self._recordings[key]
        if self._mode == "replay":
            raise MissingRecordingError(f"no recording for {key} in {self._dir}")

        started = time.perf_counter()
        response = self._api.chat.completions.create(
            model=request.model,
            messages=[{"role": role, "content": content} for role, content in request.messages],
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        recording = Recording(
            key=key,
            request=request,
            content=response.choices[0].message.content or "",
            served_model=response.model,
            usage=response.usage.model_dump(include={"prompt_tokens", "completion_tokens", "total_tokens"})
            if response.usage
            else None,
            endpoint=self._base_url,
            latency_ms=round((time.perf_counter() - started) * 1000),
            recorded_at=datetime.now(UTC),
        )
        with self._lock:
            path = self._path(request.model)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as f:
                f.write(recording.model_dump_json() + "\n")
            self._recordings[key] = recording
        return recording
