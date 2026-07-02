"""Gemini implementation of the :class:`AIProvider` port.

Uses the Google Gen AI SDK (``google-genai``), imported lazily so the rest of
the app (and the test suite, which mocks the provider) does not require the SDK
or an API key. Prompts are built here, server-side; learner-supplied text is
fenced to limit prompt injection. Quota (``429``) failures are surfaced as
:class:`AIQuotaError` so callers can degrade gracefully.
"""

from __future__ import annotations

import json
import re

from app.application.ports.ai_provider import (
    AINotConfiguredError,
    AIProviderError,
    AIQuotaError,
    AIResponse,
    GeneratedExercise,
    GeneratedLesson,
    GeneratedLessonBatch,
    GeneratedLessonPack,
    GeneratedPlacement,
    GeneratedSyllabus,
    GenerateExerciseRequest,
    GenerateLessonBatchRequest,
    GenerateLessonPackRequest,
    GenerateLessonRequest,
    GeneratePlacementRequest,
    GenerateSyllabusRequest,
    TeachRequest,
    TutorRequest,
)
from app.core.config import Settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_TEACHER_SYSTEM = (
    "You are an encouraging programming teacher. Explain concepts clearly for a "
    "{level} learner. Use short paragraphs and Markdown. Be concise."
)
_TUTOR_SYSTEM = (
    "You are a programming tutor helping a {level} learner who is stuck. Give a "
    "hint and point at the bug or next step. Do NOT provide the full solution; "
    "guide them to it. Reference their actual code. Keep it short."
)


def _fence(text: str) -> str:
    """Wrap untrusted learner text so the model treats it as data, not instructions."""
    return f"<<<\n{text.strip()}\n>>>"


class GeminiAIProvider:
    """Concrete :class:`~app.application.ports.ai_provider.AIProvider`."""

    def __init__(self, settings: Settings) -> None:
        self._api_key = settings.gemini_api_key
        self._model = settings.gemini_model
        self._teacher_model = settings.gemini_teacher_model
        self._client = None  # lazily created on first call

    def _ensure_client(self):
        if not self._api_key:
            raise AINotConfiguredError("Gemini API key is not configured")
        if self._client is None:
            try:
                from google import genai
            except ImportError as exc:  # pragma: no cover - dependency missing
                raise AIProviderError("google-genai is not installed") from exc
            self._client = genai.Client(api_key=self._api_key)
        return self._client

    def _generate(self, *, model: str, prompt: str, json_mode: bool = False) -> tuple[str, int]:
        """Call the model once; return ``(text, total_tokens)``.

        ``json_mode`` asks the model for a raw JSON response (``application/json``
        mime type), which avoids Markdown fences / prose around the JSON.
        """
        client = self._ensure_client()
        # A generated lesson pack (content + exercises with full reference
        # solutions + a quiz) is large; a small cap truncates the JSON and the
        # parse fails. Give plenty of room for structured output.
        config = (
            {"response_mime_type": "application/json", "max_output_tokens": 32768}
            if json_mode
            else None
        )
        try:
            response = client.models.generate_content(
                model=model, contents=prompt, config=config
            )
        except Exception as exc:  # noqa: BLE001 - normalize SDK errors
            message = str(exc)
            lowered = message.lower()
            if "429" in message or "resource_exhausted" in lowered or "quota" in lowered:
                logger.warning("Gemini quota exceeded: %s", message)
                # Honor the provider's suggested retry delay when present.
                match = re.search(r"retry in ([0-9.]+)s", message) or re.search(
                    r"retryDelay['\"]?:\s*['\"]?([0-9.]+)s", message
                )
                retry_after = float(match.group(1)) if match else None
                raise AIQuotaError(
                    "AI quota exceeded; try again later", retry_after=retry_after
                ) from exc
            logger.warning("Gemini request failed: %s", message)
            raise AIProviderError(f"AI request failed: {message}") from exc

        text = (getattr(response, "text", None) or "").strip()
        if not text:
            raise AIProviderError("AI returned an empty response")
        usage = getattr(response, "usage_metadata", None)
        tokens = int(getattr(usage, "total_token_count", 0) or 0)
        return text, tokens

    # ----- teaching / tutoring -----

    def teach(self, request: TeachRequest) -> AIResponse:
        system = _TEACHER_SYSTEM.format(level=request.level)
        parts = [system, f"\nTopic: {request.topic}"]
        if request.lesson_content:
            parts.append(f"\nLesson material:\n{_fence(request.lesson_content)}")
        if request.question:
            parts.append(f"\nLearner's question:\n{_fence(request.question)}")
        else:
            parts.append("\nExplain this topic for the learner.")
        text, tokens = self._generate(model=self._teacher_model, prompt="\n".join(parts))
        return AIResponse(text=text, model=self._teacher_model, total_tokens=tokens)

    def tutor(self, request: TutorRequest) -> AIResponse:
        system = _TUTOR_SYSTEM.format(level=request.level)
        parts = [system, f"\nLanguage: {request.language}"]
        if request.prompt:
            parts.append(f"\nExercise:\n{_fence(request.prompt)}")
        parts.append(f"\nLearner's current code:\n{_fence(request.code)}")
        if request.question:
            parts.append(f"\nLearner's question:\n{_fence(request.question)}")
        text, tokens = self._generate(model=self._model, prompt="\n".join(parts))
        return AIResponse(text=text, model=self._model, total_tokens=tokens)

    # ----- content generation -----

    def _generate_json(self, *, model: str, prompt: str) -> tuple[dict, int]:
        text, tokens = self._generate(model=model, prompt=prompt, json_mode=True)
        cleaned = text.strip()
        # Defensive: strip a ```json fence if the model still adds one.
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```", 2)[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
            cleaned = cleaned.strip().rstrip("`").strip()
        try:
            return json.loads(cleaned), tokens
        except json.JSONDecodeError:
            pass
        # Fallback: extract the outermost JSON object from any surrounding prose.
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start != -1 and end > start:
            try:
                return json.loads(cleaned[start : end + 1]), tokens
            except json.JSONDecodeError as exc:
                raise AIProviderError("AI returned malformed JSON") from exc
        raise AIProviderError("AI returned malformed JSON")

    def generate_lesson(self, request: GenerateLessonRequest) -> GeneratedLesson:
        prompt = (
            "Generate a short programming lesson as JSON with keys "
            '"title" (string) and "content" (Markdown string). '
            f"Topic: {request.topic}. Target level: {request.level}. "
            "Return ONLY the JSON object."
        )
        data, tokens = self._generate_json(model=self._teacher_model, prompt=prompt)
        return GeneratedLesson(
            title=str(data.get("title", request.topic)),
            content=str(data.get("content", "")),
            model=self._teacher_model,
            total_tokens=tokens,
        )

    def generate_exercise(self, request: GenerateExerciseRequest) -> GeneratedExercise:
        prompt = (
            "Generate a small coding exercise as JSON with keys: "
            '"title" (string), "prompt" (string), "starter_code" (string), '
            '"reference_solution" (a correct, complete solution in '
            f"{request.language} that reads any input from stdin and prints the "
            'answer to stdout), and "test_spec" (object with key "cases", a list '
            'of {"input": string, "expected": string}). '
            f"Topic: {request.topic}. Language: {request.language}. "
            f"Target level: {request.level}. Return ONLY the JSON object."
        )
        data, tokens = self._generate_json(model=self._model, prompt=prompt)
        test_spec = data.get("test_spec") or {}
        if not isinstance(test_spec, dict):
            test_spec = {}
        return GeneratedExercise(
            title=str(data.get("title", request.topic)),
            prompt=str(data.get("prompt", "")),
            starter_code=str(data.get("starter_code", "")),
            reference_solution=str(data.get("reference_solution", "")),
            test_spec=test_spec,
            model=self._model,
            total_tokens=tokens,
        )

    def generate_placement(self, request: GeneratePlacementRequest) -> GeneratedPlacement:
        prompt = (
            "Generate a placement test as JSON with two keys. "
            f'"mcqs": a list of {request.mcq_count} multiple-choice questions, each '
            '{"prompt": string, "choices": [{"text": string, "is_correct": boolean}]} '
            "with exactly one correct choice, ranging from easy to hard. "
            '"coding": a list of exactly 2 short coding tasks, each '
            '{"prompt": string, "starter_code": string, "reference_solution": string, '
            '"test_spec": {"cases": [{"input": string, "expected": string}]}} where the '
            f"reference_solution is a correct {request.language} program that reads any "
            "input from stdin and prints the answer to stdout. "
            "Formatting rules: in every prompt, put ALL code inside fenced Markdown "
            f"code blocks (```{request.language} ... ```) — never inline multi-line code "
            "in prose. Keep tasks simple and self-contained, and make sure each "
            "reference_solution actually produces the expected output for every test "
            "case (expected is the exact stdout, no trailing spaces). "
            f"Language: {request.language}. Return ONLY the JSON object."
        )
        data, tokens = self._generate_json(model=self._teacher_model, prompt=prompt)
        mcqs = data.get("mcqs") if isinstance(data.get("mcqs"), list) else []
        coding = data.get("coding") if isinstance(data.get("coding"), list) else []
        # Stamp the language onto each coding task for the grader.
        for task in coding:
            if isinstance(task, dict):
                task.setdefault("language", request.language)
        return GeneratedPlacement(
            mcqs=mcqs, coding=coding, model=self._teacher_model, total_tokens=tokens
        )

    def generate_syllabus(self, request: GenerateSyllabusRequest) -> GeneratedSyllabus:
        prompt = (
            "Design a course syllabus as JSON with one key "
            f'"topics": a list of {request.lesson_count} concise lesson titles for a '
            f"{request.level}-level {request.language} course, ordered from "
            "foundational to advanced, each building on the previous. "
            "Return ONLY the JSON object."
        )
        data, tokens = self._generate_json(model=self._teacher_model, prompt=prompt)
        raw = data.get("topics") if isinstance(data.get("topics"), list) else []
        topics = [str(t) for t in raw if str(t).strip()]
        return GeneratedSyllabus(
            topics=topics, model=self._teacher_model, total_tokens=tokens
        )

    def generate_lesson_pack(
        self, request: GenerateLessonPackRequest
    ) -> GeneratedLessonPack:
        prompt = (
            "Generate a complete lesson as JSON with keys: "
            '"title" (string), "content" (a Markdown lesson; put ALL code in fenced '
            f"```{request.language} code blocks), "
            f'"exercises" (a list of {request.exercise_count} coding exercises, each '
            '{"title", "prompt", "starter_code", "reference_solution", '
            '"test_spec": {"cases": [{"input": string, "expected": string}]}} where the '
            f"reference_solution is a correct {request.language} program that reads any "
            "stdin and prints the answer to stdout, and matches every expected output "
            "exactly), and "
            f'"quiz" ({{"title", "questions": [a list of {request.quiz_question_count} '
            '{"prompt", "choices": [{"text", "is_correct"}]} with exactly one correct '
            "choice each]}). "
            f"Lesson topic: {request.topic}. Language: {request.language}. Level: "
            f"{request.level}. Return ONLY the JSON object."
        )
        data, tokens = self._generate_json(model=self._teacher_model, prompt=prompt)
        exercises = data.get("exercises") if isinstance(data.get("exercises"), list) else []
        quiz = data.get("quiz") if isinstance(data.get("quiz"), dict) else {}
        return GeneratedLessonPack(
            title=str(data.get("title", request.topic)),
            content=str(data.get("content", "")),
            exercises=exercises,
            quiz=quiz,
            model=self._teacher_model,
            total_tokens=tokens,
        )

    def generate_lesson_batch(
        self, request: GenerateLessonBatchRequest
    ) -> GeneratedLessonBatch:
        prior = ""
        if request.prior_titles:
            prior = (
                " Earlier lessons already covered: "
                + "; ".join(request.prior_titles)
                + ". Continue from there with no repeats, increasing difficulty."
            )
        focus = ""
        if request.focus.strip():
            # The learner's request (possibly a short chat transcript). Infer the
            # concrete subject from it — a follow-up like "I need more" means more
            # of whatever the recent conversation was about, not a new topic.
            focus = (
                " Focus the lessons specifically on what the learner is asking for, "
                "inferring the concrete subject from this conversation (resolve vague "
                'follow-ups like "more" against the most recent topic):\n'
                + _fence(request.focus)
            )
        prompt = (
            f"Generate the next {request.count} lessons of a {request.level}-level "
            f"{request.language} course as JSON with one key "
            '"lessons": a list where each item is a complete lesson '
            '{"title" (string), "content" (Markdown; put ALL code in fenced '
            f"```{request.language} blocks), "
            f'"exercises" (a list of {request.exercise_count} coding exercises, each '
            '{"title", "prompt", "starter_code", "reference_solution", '
            '"test_spec": {"cases": [{"input": string, "expected": string}]}} whose '
            "reference_solution is correct and matches every expected stdout exactly), "
            f'and "quiz" ({{"title", "questions": [a list of '
            f"{request.quiz_question_count} "
            '{"prompt", "choices": [{"text", "is_correct"}]} with exactly one correct '
            "choice each]})}. Lessons must be ordered foundational → advanced."
            + focus
            + prior
            + " Return ONLY the JSON object."
        )
        data, tokens = self._generate_json(model=self._teacher_model, prompt=prompt)
        lessons = data.get("lessons") if isinstance(data.get("lessons"), list) else []
        return GeneratedLessonBatch(
            lessons=lessons, model=self._teacher_model, total_tokens=tokens
        )
