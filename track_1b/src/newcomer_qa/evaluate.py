import json
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, model_validator

from newcomer_qa.build import TestCase
from newcomer_qa.client import ChatRequest, Mode, RecordingClient
from newcomer_qa.config import Settings

Grade = Literal["correct", "incorrect", "not_attempted"]
GRADE_LETTERS: dict[str, Grade] = {"A": "correct", "B": "incorrect", "C": "not_attempted"}


class Sampling(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    temperature: float
    max_tokens: int


class Judge(Sampling):
    model: str


class EvalConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    endpoint: str
    models: dict[str, str]
    # Condition name -> language -> sentence put before the question; an empty mapping asks the bare question.
    conditions: dict[str, dict[str, str]]
    main_condition: str
    answer: Sampling
    judge: Judge
    # Grades in data/grades/<primary_grader>.jsonl are the headline; the judge above is the in-harness comparison.
    primary_grader: str

    @model_validator(mode="after")
    def _main_condition_is_listed(self) -> "EvalConfig":
        if self.main_condition not in self.conditions:
            raise ValueError(f"main_condition {self.main_condition!r} is not one of {list(self.conditions)}")
        return self

    @classmethod
    def load(cls, path: Path) -> "EvalConfig":
        with path.open(encoding="utf-8") as f:
            return cls.model_validate(yaml.safe_load(f))


class Response(BaseModel):
    item_id: str
    lang: str
    topic: str
    model: str
    condition: str
    response: str
    # From the primary grader's committed grades; None for a response it has not graded yet.
    grade: Grade | None
    judge_grade: Grade | None
    judge_output: str

    @property
    def key(self) -> str:
        return f"{self.model}/{self.condition}/{self.item_id}"


def load_test_cases(path: Path) -> list[TestCase]:
    with path.open(encoding="utf-8") as f:
        return [TestCase.model_validate_json(line) for line in f if line.strip()]


def gold_target(case: TestCase) -> str:
    first, *others = case.answers
    return f"{first} (also acceptable: {'; '.join(others)})" if others else first


def parse_grade(text: str) -> Grade | None:
    # Same rule as simple-evals: the first A, B or C anywhere in the judge's reply.
    match = re.search(r"(A|B|C)", text)
    return GRADE_LETTERS[match.group(1)] if match else None


class GradeRecord(BaseModel):
    key: str
    grade: Grade


def load_grades(path: Path) -> dict[str, Grade]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        return {g.key: g.grade for g in (GradeRecord.model_validate_json(line) for line in f if line.strip())}


def evaluate(settings: Settings, mode: Mode) -> list[Response]:
    config = EvalConfig.load(settings.eval_config)
    client = RecordingClient(settings.model_copy(update={"llm_base_url": config.endpoint}), settings.recordings_dir, mode)
    grader = settings.grader_prompt.read_text(encoding="utf-8")
    cases = load_test_cases(settings.dataset_dir / "test_cases.jsonl")
    primary = load_grades(settings.grades_dir / f"{config.primary_grader}.jsonl")

    def respond(job: tuple[str, str, TestCase]) -> Response:
        name, condition, case = job
        context = config.conditions[condition].get(case.lang)
        answer = client.chat(
            ChatRequest(
                model=config.models[name],
                messages=(("user", f"{context} {case.question}" if context else case.question),),
                temperature=config.answer.temperature,
                max_tokens=config.answer.max_tokens,
            )
        ).content
        prompt = grader.format(question=case.question, target=gold_target(case), predicted_answer=answer)
        verdict = client.chat(
            ChatRequest(
                model=config.judge.model,
                messages=(("user", prompt),),
                temperature=config.judge.temperature,
                max_tokens=config.judge.max_tokens,
            )
        ).content
        key = f"{name}/{condition}/{case.item_id}"
        return Response(
            item_id=case.item_id,
            lang=case.lang,
            topic=case.topic,
            model=name,
            condition=condition,
            response=answer,
            grade=primary.get(key),
            judge_grade=parse_grade(verdict),
            judge_output=verdict,
        )

    jobs = [(name, condition, case) for condition in config.conditions for name in config.models for case in cases]
    with ThreadPoolExecutor(max_workers=settings.concurrency) as pool:
        responses = list(pool.map(respond, jobs))
    settings.responses.parent.mkdir(parents=True, exist_ok=True)
    with settings.responses.open("w", encoding="utf-8") as f:
        f.writelines(json.dumps(r.model_dump(), ensure_ascii=False) + "\n" for r in responses)
    ungraded = sum(r.grade is None for r in responses)
    if ungraded:
        print(f"{ungraded} responses have no {config.primary_grader} grade yet; see the judge_grade columns")
    return responses
