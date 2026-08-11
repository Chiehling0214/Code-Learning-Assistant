import uuid
from datetime import UTC, datetime

from app.application.services.mastery_service import Evidence, score_evidence


def test_coding_evidence_has_more_weight_than_quiz_evidence() -> None:
    now = datetime.now(UTC)
    accuracy, coding, quiz, confidence, sample = score_evidence(
        [
            Evidence(uuid.uuid4(), "exercise", 1, now),
            Evidence(uuid.uuid4(), "quiz", 0, now),
        ]
    )

    assert accuracy == 67
    assert coding == 2
    assert quiz == 1
    assert confidence == "medium"
    assert sample == "developing"


def test_retry_cannot_erase_a_failed_first_attempt() -> None:
    now = datetime.now(UTC)
    item_id = uuid.uuid4()
    accuracy, *_ = score_evidence(
        [
            Evidence(item_id, "exercise", 0, now),
            Evidence(item_id, "exercise", 1, now),
            Evidence(item_id, "exercise", 1, now),
        ]
    )

    assert accuracy is not None
    assert accuracy < 60
