import pytest
from pydantic import ValidationError
from app.models.enums import RecoveryAction
from app.models.guardrails.guardrail_result import GuardrailResult

def test_valid_non_overridden_result():
    """
    A guardrail result is valid when the original and final actions are the same, was_overridden is False, and there is no reason.
    """

    result = GuardrailResult(
        original_action=RecoveryAction.RETRY,
        final_action=RecoveryAction.RETRY,
        was_overridden=False,
        override_reason=None
    )

    assert result.original_action == RecoveryAction.RETRY
    assert result.final_action == RecoveryAction.RETRY
    assert result.was_overridden is False
    assert result.override_reason is None


def test_valid_overridden_result():
    """
    A guardrail result is valid when the final action differs from the original action and a reason for the override is provided.
    """

    result = GuardrailResult(
        original_action=RecoveryAction.RETRY,
        final_action=RecoveryAction.ESCALATE,
        was_overridden=True,
        override_reason="Maximum retry limit reached"
    )

    assert result.original_action == RecoveryAction.RETRY
    assert result.final_action == RecoveryAction.ESCALATE
    assert result.was_overridden is True
    assert result.override_reason == "Maximum retry limit reached"


def test_same_actions_cannot_be_marked_as_overridden():
    """
    If the original and final actions are the same, the decision cannot be marked as overridden.
    """

    with pytest.raises(ValidationError):
        GuardrailResult(
            original_action=RecoveryAction.RETRY,
            final_action=RecoveryAction.RETRY,
            was_overridden=True,
            override_reason="Retry policy checked"
        )


def test_same_actions_cannot_have_override_reason():
    """
    If no override occurred, there should not be a reason claiming that an override happened.
    """

    with pytest.raises(ValidationError):
        GuardrailResult(
            original_action=RecoveryAction.NOTIFY,
            final_action=RecoveryAction.NOTIFY,
            was_overridden=False,
            override_reason="Some guardrail reason"
        )


def test_different_actions_require_override_flag():
    """
    If the original and final actions differ, the decision must be marked as overridden.
    """

    with pytest.raises(ValidationError):
        GuardrailResult(
            original_action=RecoveryAction.RETRY,
            final_action=RecoveryAction.ESCALATE,
            was_overridden=False,
            override_reason="Maximum retry limit reached"
        )


def test_override_requires_reason():
    """
    If an override occurs, the system must record why the original action was changed.
    """

    with pytest.raises(ValidationError):
        GuardrailResult(
            original_action=RecoveryAction.RETRY,
            final_action=RecoveryAction.STOP,
            was_overridden=True,
            override_reason=None
        )


def test_override_cannot_have_empty_reason():
    """
    An empty string is not a meaningful explanation for why the guardrail changed the LLM's proposed action.
    """

    with pytest.raises(ValidationError):
        GuardrailResult(
            original_action=RecoveryAction.RETRY,
            final_action=RecoveryAction.STOP,
            was_overridden=True,
            override_reason=""
        )