"""Tests for code execution and grading (mocked Judge0 runner, no network)."""

import uuid
from types import SimpleNamespace

from app.api.deps import get_current_db_user
from app.application.services.execution_service import ExecutionService
from app.main import app
from fastapi.testclient import TestClient

from tests.fakes import FakeCodeRunner as Runner

TEST_SPEC = {"cases": [{"input": "", "expected": "hi"}]}


# ----- grading algorithm (unit) -----


def test_grade_passes_on_match() -> None:
    runner = Runner()
    runner.set(stdout="hi\n", status_id=3, status="Accepted")
    status, result = ExecutionService(runner).grade(
        code="...", language="python", test_spec=TEST_SPEC
    )
    assert status == "passed"
    assert result["passed"] == 1 and result["total"] == 1


def test_grade_fails_on_mismatch() -> None:
    runner = Runner()
    runner.set(stdout="bye", status_id=3, status="Accepted")
    status, result = ExecutionService(runner).grade(
        code="...", language="python", test_spec=TEST_SPEC
    )
    assert status == "failed"
    assert result["passed"] == 0


def test_grade_error_on_runtime_error() -> None:
    runner = Runner()
    runner.set(stdout="", status_id=11, status="Runtime Error (NZEC)")
    status, _ = ExecutionService(runner).grade(
        code="...", language="python", test_spec=TEST_SPEC
    )
    assert status == "error"


def test_grade_error_on_compile_error() -> None:
    runner = Runner()
    runner.set(status_id=6, status="Compilation Error", compile_output="boom")
    status, result = ExecutionService(runner).grade(
        code="...", language="cpp", test_spec=TEST_SPEC
    )
    assert status == "error"
    assert result["compile_output"] == "boom"


def test_grade_error_when_runner_unavailable() -> None:
    runner = Runner()
    runner.raise_error = True
    status, result = ExecutionService(runner).grade(
        code="...", language="python", test_spec=TEST_SPEC
    )
    assert status == "error"
    assert "error" in result


def test_grade_error_when_no_test_cases() -> None:
    status, _ = ExecutionService(Runner()).grade(code="...", language="python", test_spec={})
    assert status == "error"


def test_grade_hides_hidden_case_io() -> None:
    runner = Runner()
    runner.set(stdout="x", status_id=3, status="Accepted")
    spec = {"cases": [{"input": "secret", "expected": "y", "hidden": True}]}
    _, result = ExecutionService(runner).grade(code="...", language="python", test_spec=spec)
    entry = result["tests"][0]
    assert "input" not in entry and "expected" not in entry
    assert "passed" in entry


# ----- /run endpoint -----


def test_run_returns_stdout(client: TestClient, fakes: SimpleNamespace) -> None:
    fakes.runner.set(stdout="hello\n", status="Accepted")
    exercise = fakes.exercises.create(
        lesson_id=uuid.uuid4(),
        language="python",
        title="E",
        slug="e",
        prompt="",
        starter_code="",
        test_spec={},
    )
    res = client.post(f"/api/v1/exercises/{exercise.id}/run", json={"code": "print('hello')"})
    assert res.status_code == 200
    assert res.json()["stdout"] == "hello\n"


def test_run_degrades_when_judge0_unavailable(
    client: TestClient, fakes: SimpleNamespace
) -> None:
    fakes.runner.raise_error = True
    exercise = fakes.exercises.create(
        lesson_id=uuid.uuid4(),
        language="python",
        title="E",
        slug="e",
        prompt="",
        starter_code="",
        test_spec={},
    )
    res = client.post(f"/api/v1/exercises/{exercise.id}/run", json={"code": "x"})
    assert res.status_code == 200  # graceful, not a 500
    assert res.json()["error"] is not None


# ----- GET /submissions/{id} -----


def test_get_submission_returns_owned(client: TestClient, fakes: SimpleNamespace) -> None:
    submission = fakes.submissions.create(
        user_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        exercise_id=uuid.uuid4(),
        code="x",
    )
    owner = _user(submission.user_id)
    app.dependency_overrides[get_current_db_user] = lambda: owner
    res = client.get(f"/api/v1/submissions/{submission.id}")
    assert res.status_code == 200
    assert res.json()["status"] == "pending"


def test_get_submission_404_for_non_owner(client: TestClient, fakes: SimpleNamespace) -> None:
    submission = fakes.submissions.create(
        user_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        exercise_id=uuid.uuid4(),
        code="x",
    )
    other = _user(uuid.uuid4())
    app.dependency_overrides[get_current_db_user] = lambda: other
    res = client.get(f"/api/v1/submissions/{submission.id}")
    assert res.status_code == 404


def _user(user_id: uuid.UUID):
    from datetime import UTC, datetime

    from app.domain.entities import User

    now = datetime.now(UTC)
    return User(
        id=user_id,
        firebase_uid=str(user_id),
        email="u@x.com",
        display_name=None,
        is_admin=False,
        created_at=now,
        updated_at=now,
    )
