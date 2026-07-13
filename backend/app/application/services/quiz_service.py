"""Quiz use cases.

Learners read a quiz (answer keys stripped at the API layer) and submit answers
for auto-grading; admins author quizzes. Depends only on domain repository
interfaces. Raises :class:`LookupError` for missing entities (mapped to ``404``)
and :class:`ValueError` for invalid authoring input (mapped to ``400``).
"""

from __future__ import annotations

import uuid
from typing import Any

from app.application.services.review_service import ReviewService
from app.domain.entities import Question, Quiz, QuizAttempt
from app.domain.repositories import (
    LessonRepository,
    ProgressRepository,
    QuizAttemptRepository,
    QuizRepository,
)


class QuizService:
    def __init__(
        self,
        quizzes: QuizRepository,
        attempts: QuizAttemptRepository,
        lessons: LessonRepository,
        progress: ProgressRepository | None = None,
        reviews: ReviewService | None = None,
    ) -> None:
        self._quizzes = quizzes
        self._attempts = attempts
        self._lessons = lessons
        self._progress = progress
        self._reviews = reviews

    # ----- reads -----

    def get_quiz(self, quiz_id: uuid.UUID) -> Quiz:
        quiz = self._quizzes.get_by_id(quiz_id)
        if quiz is None:
            raise LookupError(f"Quiz {quiz_id} not found")
        return quiz

    def list_for_lesson(self, lesson_id: uuid.UUID) -> list[Quiz]:
        return self._quizzes.list_by_lesson(lesson_id)

    def list_attempts(self, *, user_id: uuid.UUID, quiz_id: uuid.UUID) -> list[QuizAttempt]:
        return self._attempts.list_for_user_and_quiz(user_id, quiz_id)

    # ----- grading -----

    def grade(
        self, *, user_id: uuid.UUID, quiz_id: uuid.UUID, answers: dict[uuid.UUID, uuid.UUID]
    ) -> tuple[QuizAttempt, int, list[dict[str, Any]]]:
        """Grade submitted answers, persist a :class:`QuizAttempt`, return detail.

        ``answers`` maps ``question_id -> selected choice_id``. Returns
        ``(attempt, total, results)`` where ``results`` holds per-question
        correctness (with the correct choice revealed for learner feedback).
        """
        quiz = self.get_quiz(quiz_id)

        results: list[dict[str, Any]] = []
        score = 0
        for question in quiz.questions:
            correct_choice = next((c for c in question.choices if c.is_correct), None)
            correct_id = correct_choice.id if correct_choice else None
            selected_id = answers.get(question.id)
            is_correct = selected_id is not None and selected_id == correct_id
            if is_correct:
                score += 1
            elif self._reviews is not None:
                # A miss enters the spaced-review notebook (snapshot survives
                # later content edits/hiding).
                self._reviews.capture_miss(
                    user_id=user_id,
                    source="quiz",
                    item_ref=question.id,
                    payload={
                        "kind": "mcq",
                        "prompt": question.prompt,
                        "choices": [
                            {"id": str(c.id), "text": c.text, "is_correct": c.is_correct}
                            for c in question.choices
                        ],
                        "explanation": question.explanation,
                        "quiz_id": str(quiz.id),
                        "quiz_title": quiz.title,
                    },
                )
            results.append(
                {
                    "question_id": str(question.id),
                    "correct": is_correct,
                    "selected_choice_id": str(selected_id) if selected_id else None,
                    "correct_choice_id": str(correct_id) if correct_id else None,
                    "explanation": question.explanation,
                }
            )

        total = len(quiz.questions)
        stored = {
            "selected": {str(q): str(c) for q, c in answers.items()},
            "total": total,
            "results": results,
        }
        attempt = self._attempts.create(
            user_id=user_id, quiz_id=quiz_id, score=score, answers=stored
        )
        if self._progress is not None:
            # Taking a quiz counts as completing it (progress tracking, Sprint 7).
            self._progress.record(
                user_id=user_id,
                item_type="quiz",
                item_id=quiz_id,
                status="completed",
                score=score,
            )
        return attempt, total, results

    # ----- authoring (admin) -----

    def create_quiz(
        self, *, lesson_id: uuid.UUID, title: str, slug: str, description: str | None
    ) -> Quiz:
        if self._lessons.get_by_id(lesson_id) is None:
            raise LookupError(f"Lesson {lesson_id} not found")
        return self._quizzes.create(
            lesson_id=lesson_id, title=title, slug=slug, description=description
        )

    def add_question(
        self,
        *,
        quiz_id: uuid.UUID,
        prompt: str,
        type: str,
        order_index: int,
        choices: list[dict],
        explanation: str = "",
    ) -> Question:
        if self._quizzes.get_by_id(quiz_id) is None:
            raise LookupError(f"Quiz {quiz_id} not found")
        if len(choices) < 2:
            raise ValueError("A question needs at least two choices")
        if not any(c.get("is_correct") for c in choices):
            raise ValueError("A question needs at least one correct choice")
        return self._quizzes.add_question(
            quiz_id=quiz_id,
            prompt=prompt,
            type=type,
            order_index=order_index,
            choices=choices,
            explanation=explanation,
        )

    def delete_quiz(self, quiz_id: uuid.UUID) -> None:
        self._quizzes.delete(quiz_id)
