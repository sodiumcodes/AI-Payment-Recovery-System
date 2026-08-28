import pytest
from pydantic import ValidationError
from app.models.decisions.recovery_decision import RecoveryDecision
from app.models.enums import RecoveryAction

#A retry decision is valid when it includes a positive retry_after_minutes value.
def test_valid_retry_decision():
    
    decision = RecoveryDecision(
        action=RecoveryAction.RETRY,
        retry_after_minutes=30,
        reason="The failure appears temporary.",
        confidence=0.9
    )

    assert decision.action == RecoveryAction.RETRY
    assert decision.retry_after_minutes == 30
    assert decision.reason == "The failure appears temporary."
    assert decision.confidence == 0.9

#A non-retry action is valid when retry_after_minutes is None.
def test_valid_non_retry_decision():

    decision = RecoveryDecision(
        action=RecoveryAction.ESCALATE,
        retry_after_minutes=None,
        reason="Repeated failures require escalation.",
        confidence=0.95
    )

    assert decision.action == RecoveryAction.ESCALATE
    assert decision.retry_after_minutes is None

#The action must belong to the predefined RecoveryAction enum.
def test_invalid_action_is_rejected():

    with pytest.raises(ValidationError):
        RecoveryDecision(
            action="try_again",
            retry_after_minutes=None,
            reason="Trying another action.",
            confidence=0.8
        )

#A retry decision must specify when the retry should happen.
def test_retry_requires_retry_after_minutes():

    with pytest.raises(ValidationError):
        RecoveryDecision(
            action=RecoveryAction.RETRY,
            retry_after_minutes=None,
            reason="The failure appears temporary.",
            confidence=0.9
        )

#Retry timing must be greater than zero when the action is retry.
def test_retry_after_minutes_must_be_positive():

    with pytest.raises(ValidationError):
        RecoveryDecision(
            action=RecoveryAction.RETRY,
            retry_after_minutes=0,
            reason="The failure appears temporary.",
            confidence=0.9
        )

#A retry cannot be scheduled using a negative delay.
def test_negative_retry_after_minutes_is_rejected():

    with pytest.raises(ValidationError):
        RecoveryDecision(
            action=RecoveryAction.RETRY,
            retry_after_minutes=-10,
            reason="The failure appears temporary.",
            confidence=0.9
        )

#Actions other than retry must not contain retry timing, because that would create contradictory decision data.
def test_non_retry_action_cannot_have_retry_timing():
    
    with pytest.raises(ValidationError):
        RecoveryDecision(
            action=RecoveryAction.ESCALATE,
            retry_after_minutes=30,
            reason="Repeated failures require escalation.",
            confidence=0.95
        )

#Every decision must contain an explanation for auditing and debugging purposes.
def test_reason_cannot_be_empty():

    with pytest.raises(ValidationError):
        RecoveryDecision(
            action=RecoveryAction.STOP,
            retry_after_minutes=None,
            reason="",
            confidence=0.8
        )

#Confidence must remain within the range 0.0 to 1.0.
def test_confidence_cannot_be_less_than_zero():

    with pytest.raises(ValidationError):
        RecoveryDecision(
            action=RecoveryAction.NOTIFY,
            retry_after_minutes=None,
            reason="Customer should be notified.",
            confidence=-0.1
        )

#Confidence must remain within the range 0.0 to 1.0.
def test_confidence_cannot_exceed_one():

    with pytest.raises(ValidationError):
        RecoveryDecision(
            action=RecoveryAction.NOTIFY,
            retry_after_minutes=None,
            reason="Customer should be notified.",
            confidence=1.1
        )