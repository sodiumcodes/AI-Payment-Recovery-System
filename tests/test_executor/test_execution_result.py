import pytest
from pydantic import ValidationError
from app.models.enums import ExecutionStatus, RecoveryAction
from app.models.execution.execution_result import ExecutionResult

def test_valid_successful_execution():
    """
    A successfully executed action must have the EXECUTED status.
    """

    result = ExecutionResult(
        action=RecoveryAction.RETRY,
        executed=True,
        status=ExecutionStatus.EXECUTED,
        message="Retry executed successfully."
    )

    assert result.action == RecoveryAction.RETRY
    assert result.executed is True
    assert result.status == ExecutionStatus.EXECUTED
    assert result.message == "Retry executed successfully."


def test_valid_failed_execution():
    """
    A failed action execution must have the FAILED status.
    """

    result = ExecutionResult(
        action=RecoveryAction.NOTIFY,
        executed=False,
        status=ExecutionStatus.FAILED,
        message="Notification service was unavailable."
    )

    assert result.action == RecoveryAction.NOTIFY
    assert result.executed is False
    assert result.status == ExecutionStatus.FAILED


def test_invalid_action_is_rejected():
    """
    The action must belong to the predefined RecoveryAction enum.
    """

    with pytest.raises(ValidationError):
        ExecutionResult(
            action="unknown_action",
            executed=True,
            status=ExecutionStatus.EXECUTED,
            message="Action completed."
        )


def test_invalid_status_is_rejected():
    """
    The status must belong to the predefined ExecutionStatus enum.
    """

    with pytest.raises(ValidationError):
        ExecutionResult(
            action=RecoveryAction.RETRY,
            executed=True,
            status="success",
            message="Retry completed."
        )


def test_successful_execution_requires_executed_status():
    """
    executed=True cannot be combined with a FAILED status.
    """

    with pytest.raises(ValidationError):
        ExecutionResult(
            action=RecoveryAction.RETRY,
            executed=True,
            status=ExecutionStatus.FAILED,
            message="Contradictory execution result."
        )


def test_failed_execution_requires_failed_status():
    """
    executed=False cannot be combined with an EXECUTED status.
    """

    with pytest.raises(ValidationError):
        ExecutionResult(
            action=RecoveryAction.NOTIFY,
            executed=False,
            status=ExecutionStatus.EXECUTED,
            message="Contradictory execution result."
        )


def test_message_cannot_be_empty():
    """
    Every execution result must contain a meaningful message.
    """

    with pytest.raises(ValidationError):
        ExecutionResult(
            action=RecoveryAction.STOP,
            executed=True,
            status=ExecutionStatus.EXECUTED,
            message=""
        )