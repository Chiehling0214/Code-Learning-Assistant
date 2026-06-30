"""Code execution and grading use cases.

Depends on a :class:`CodeRunner` port (implemented by the Judge0 client) so the
grading algorithm is framework- and provider-agnostic and easily testable with a
fake runner.
"""

from __future__ import annotations

from typing import Any, Protocol

from app.infrastructure.judge0.client import Judge0Error

# Judge0 status ids we care about.
_ACCEPTED = 3
_COMPILE_ERROR = 6
_RUNTIME_ERROR_RANGE = range(7, 14)  # 7..13: runtime + internal errors


class CodeRunner(Protocol):
    def execute(self, source_code: str, language: str, stdin: str = "") -> dict: ...


class ExecutionService:
    def __init__(self, runner: CodeRunner) -> None:
        self._runner = runner

    def run(self, *, code: str, language: str, stdin: str = "") -> dict:
        """Run code once (no grading) for the editor's Run button.

        Returns a result dict, or ``{"error": ...}`` if execution is unavailable.
        """
        try:
            return self._runner.execute(code, language, stdin)
        except Judge0Error as exc:
            return {
                "error": str(exc),
                "stdout": "",
                "stderr": "",
                "status": "Execution unavailable",
            }

    def grade(
        self, *, code: str, language: str, test_spec: dict[str, Any]
    ) -> tuple[str, dict[str, Any]]:
        """Run ``code`` against each test case and return ``(status, result)``.

        ``status`` is one of ``passed`` | ``failed`` | ``error``. Hidden test
        cases (``"hidden": true``) expose only pass/fail, never their I/O.
        """
        cases = (test_spec or {}).get("cases") or []
        if not cases:
            return "error", {
                "verdict": "error",
                "error": "Exercise has no test cases",
                "passed": 0,
                "total": 0,
                "tests": [],
            }

        tests: list[dict[str, Any]] = []
        passed = 0
        had_runtime_error = False

        for index, case in enumerate(cases):
            stdin = str(case.get("input", ""))
            expected = str(case.get("expected", "")).strip()
            hidden = bool(case.get("hidden", False))

            try:
                res = self._runner.execute(code, language, stdin)
            except Judge0Error as exc:
                # Infrastructure failure: cannot grade -> error verdict.
                return "error", {
                    "verdict": "error",
                    "error": str(exc),
                    "passed": passed,
                    "total": len(cases),
                    "tests": tests,
                }

            status_id = res.get("status_id")

            if status_id == _COMPILE_ERROR:
                return "error", {
                    "verdict": "error",
                    "error": "Compilation error",
                    "compile_output": res.get("compile_output"),
                    "passed": 0,
                    "total": len(cases),
                    "tests": [],
                }

            actual = (res.get("stdout") or "").strip()
            if status_id in _RUNTIME_ERROR_RANGE:
                had_runtime_error = True
                ok = False
            else:
                ok = status_id == _ACCEPTED and actual == expected

            if ok:
                passed += 1

            entry: dict[str, Any] = {"index": index, "passed": ok, "status": res.get("status")}
            if not hidden:
                entry.update(
                    {
                        "input": stdin,
                        "expected": expected,
                        "actual": actual,
                        "stderr": res.get("stderr") or "",
                    }
                )
            tests.append(entry)

        if had_runtime_error:
            verdict = "error"
        elif passed == len(cases):
            verdict = "passed"
        else:
            verdict = "failed"

        return verdict, {
            "verdict": verdict,
            "passed": passed,
            "total": len(cases),
            "tests": tests,
        }
