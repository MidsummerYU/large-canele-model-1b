from types import SimpleNamespace

import pytest

from newcomer_qa.client import ChatRequest, MissingRecordingError, RecordingClient
from newcomer_qa.config import Settings


class FakeApi:
    def __init__(self):
        self.calls = 0
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **_):
        self.calls += 1
        return SimpleNamespace(
            model="served-model",
            choices=[SimpleNamespace(message=SimpleNamespace(content="14 days"))],
            usage=None,
        )


SETTINGS = Settings(llm_base_url="http://example.invalid/v1")
REQUEST = ChatRequest(model="org/model-70B", messages=(("user", "?"),), temperature=0.0, max_tokens=8)


def test_live_call_is_recorded_and_then_replayed_without_the_api(tmp_path):
    api = FakeApi()
    assert RecordingClient(SETTINGS, tmp_path, "live", api).chat(REQUEST).content == "14 days"
    assert RecordingClient(SETTINGS, tmp_path, "replay").chat(REQUEST).content == "14 days"
    assert api.calls == 1


def test_replay_refuses_to_call_the_api(tmp_path):
    with pytest.raises(MissingRecordingError):
        RecordingClient(SETTINGS, tmp_path, "replay").chat(REQUEST)
