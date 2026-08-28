from datetime import datetime
import pytest
from pydantic import ValidationError
from app.models.context.retry_history import RetryHistory

def test_valid_retry_history():
    #A retry history with valid values should be created successfully.

    history = RetryHistory(
        payment_id="pay_001",
        total_attempts=3,
        successful_retries=1,
        failed_retries=2,
        last_retry_at=datetime.now()
    )

    assert history.payment_id == "pay_001"
    assert history.total_attempts == 3
    assert history.successful_retries == 1
    assert history.failed_retries == 2
    assert history.last_retry_at is not None


def test_payment_id_cannot_be_empty():
    #Every retry history must belong to a specific payment.

    with pytest.raises(ValidationError):
        RetryHistory(
            payment_id="",
            total_attempts=1,
            successful_retries=0,
            failed_retries=1,
            last_retry_at=datetime.now()
        )


def test_total_attempts_cannot_be_negative():
    #The total number of retry attempts cannot be negative.
    
    with pytest.raises(ValidationError):
        RetryHistory(
            payment_id="pay_001",
            total_attempts=-1,
            successful_retries=0,
            failed_retries=0,
            last_retry_at=None
        )


def test_successful_retries_cannot_be_negative():
    #The number of successful retries cannot be negative.
    
    with pytest.raises(ValidationError):
        RetryHistory(
            payment_id="pay_001",
            total_attempts=1,
            successful_retries=-1,
            failed_retries=1,
            last_retry_at=datetime.now()
        )


def test_failed_retries_cannot_be_negative():
    #The number of failed retries cannot be negative.
    
    with pytest.raises(ValidationError):
        RetryHistory(
            payment_id="pay_001",
            total_attempts=1,
            successful_retries=0,
            failed_retries=-1,
            last_retry_at=datetime.now()
        )


def test_outcomes_cannot_exceed_total_attempts():
    #Successful and failed retries together cannot exceed the total number of retry attempts.
    
    with pytest.raises(ValidationError):
        RetryHistory(
            payment_id="pay_001",
            total_attempts=2,
            successful_retries=1,
            failed_retries=2,
            last_retry_at=datetime.now()
        )


def test_zero_attempts_cannot_have_last_retry_timestamp():
    #If no retry has been attempted, there cannot be a timestamp representing the most recent retry.
    
    with pytest.raises(ValidationError):
        RetryHistory(
            payment_id="pay_001",
            total_attempts=0,
            successful_retries=0,
            failed_retries=0,
            last_retry_at=datetime.now()
        )


def test_attempts_require_last_retry_timestamp():
    #If one or more retries have been attempted, the timestamp of the most recent retry is required.

    with pytest.raises(ValidationError):
        RetryHistory(
            payment_id="pay_001",
            total_attempts=2,
            successful_retries=0,
            failed_retries=2,
            last_retry_at=None
        )


def test_unresolved_retry_outcomes_are_allowed():
    """
    Successful and failed retries do not need to equal total attempts.

    Some retry attempts may have unresolved outcomes, such as pending or timed-out retries.
    """

    history = RetryHistory(
        payment_id="pay_001",
        total_attempts=5,
        successful_retries=1,
        failed_retries=3,
        last_retry_at=datetime.now()
    )

    assert history.total_attempts == 5
    assert history.successful_retries == 1
    assert history.failed_retries == 3