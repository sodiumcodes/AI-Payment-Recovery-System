from datetime import datetime

import pytest
from pydantic import ValidationError

from app.models.audit.audit_log import AuditLog
from app.models.context.customer_history import CustomerHistory
from app.models.context.payment_method_status import PaymentMethodStatus
from app.models.context.retry_history import RetryHistory
from app.models.decisions.recovery_decision import RecoveryDecision
from app.models.enums import (
    FailureType,
    PaymentMethodStatusType,
    RecoveryAction,
    ExecutionStatus,
)
from app.models.events.payment_failed import PaymentFailedEvent
from app.models.execution.execution_result import ExecutionResult
from app.models.guardrails.guardrail_result import GuardrailResult


def create_valid_audit_log():
    """
    Creates a complete valid recovery workflow.

    This helper avoids repeating the same setup in multiple tests.
    """

    event = PaymentFailedEvent(
        event_id="event_001",
        event_type="payment_failed",
        payment_id="pay_001",
        customer_id="cust_001",
        amount=1000,
        currency="INR",
        failure_type=FailureType.NETWORK_TIMEOUT,
        retry_count=1,
        total_failures=2,
        timestamp=datetime.now()
    )

    customer_history = CustomerHistory(
        customer_id="cust_001",
        total_successful_payments=10,
        total_failed_payments=2,
        previous_recoveries=1,
        last_successful_payment_at=datetime.now()
    )

    retry_history = RetryHistory(
        payment_id="pay_001",
        total_attempts=1,
        successful_retries=0,
        failed_retries=1,
        last_retry_at=datetime.now()
    )

    payment_method_status = PaymentMethodStatus(
        payment_id="pay_001",
        status=PaymentMethodStatusType.ACTIVE,
        can_retry=True,
        reason_if_not_retryable=None
    )

    proposed_decision = RecoveryDecision(
        action=RecoveryAction.RETRY,
        retry_after_minutes=30,
        reason="The failure appears temporary.",
        confidence=0.9
    )

    guardrail_result = GuardrailResult(
        original_action=RecoveryAction.RETRY,
        final_action=RecoveryAction.RETRY,
        was_overridden=False,
        override_reason=None
    )

    execution_result = ExecutionResult(
        action=RecoveryAction.RETRY,
        executed=True,
        status=ExecutionStatus.EXECUTED,
        message="Retry executed successfully."
    )

    return AuditLog(
        audit_id="audit_001",
        timestamp=datetime.now(),
        event=event,
        customer_history=customer_history,
        retry_history=retry_history,
        payment_method_status=payment_method_status,
        proposed_decision=proposed_decision,
        guardrail_result=guardrail_result,
        execution_result=execution_result
    )


def test_valid_audit_log():
    """
    A complete recovery workflow containing valid nested contracts
    should create an AuditLog successfully.
    """

    audit_log = create_valid_audit_log()

    assert audit_log.audit_id == "audit_001"
    assert audit_log.event.payment_id == "pay_001"
    assert audit_log.customer_history.customer_id == "cust_001"
    assert audit_log.retry_history.total_attempts == 1
    assert audit_log.payment_method_status.can_retry is True
    assert audit_log.proposed_decision.action == RecoveryAction.RETRY
    assert audit_log.guardrail_result.final_action == RecoveryAction.RETRY
    assert audit_log.execution_result.executed is True


def test_audit_id_cannot_be_empty():
    """
    Every audit record must have a unique, non-empty identifier.
    """

    audit_log = create_valid_audit_log()

    with pytest.raises(ValidationError):
        AuditLog(
            audit_id="",
            timestamp=audit_log.timestamp,
            event=audit_log.event,
            customer_history=audit_log.customer_history,
            retry_history=audit_log.retry_history,
            payment_method_status=audit_log.payment_method_status,
            proposed_decision=audit_log.proposed_decision,
            guardrail_result=audit_log.guardrail_result,
            execution_result=audit_log.execution_result
        )


def test_audit_log_requires_event():
    """
    The original event is required because every audit record must
    be traceable back to what triggered the recovery workflow.
    """

    audit_log = create_valid_audit_log()

    with pytest.raises(ValidationError):
        AuditLog(
            audit_id="audit_002",
            timestamp=audit_log.timestamp,
            customer_history=audit_log.customer_history,
            retry_history=audit_log.retry_history,
            payment_method_status=audit_log.payment_method_status,
            proposed_decision=audit_log.proposed_decision,
            guardrail_result=audit_log.guardrail_result,
            execution_result=audit_log.execution_result
        )


def test_audit_log_requires_customer_history():
    """
    The audit record should contain the customer context used by
    the agent when making the decision.
    """

    audit_log = create_valid_audit_log()

    with pytest.raises(ValidationError):
        AuditLog(
            audit_id="audit_002",
            timestamp=audit_log.timestamp,
            event=audit_log.event,
            retry_history=audit_log.retry_history,
            payment_method_status=audit_log.payment_method_status,
            proposed_decision=audit_log.proposed_decision,
            guardrail_result=audit_log.guardrail_result,
            execution_result=audit_log.execution_result
        )


def test_audit_log_requires_proposed_decision():
    """
    The audit record must contain the decision originally proposed
    by the LLM so that the workflow remains explainable.
    """

    audit_log = create_valid_audit_log()

    with pytest.raises(ValidationError):
        AuditLog(
            audit_id="audit_002",
            timestamp=audit_log.timestamp,
            event=audit_log.event,
            customer_history=audit_log.customer_history,
            retry_history=audit_log.retry_history,
            payment_method_status=audit_log.payment_method_status,
            guardrail_result=audit_log.guardrail_result,
            execution_result=audit_log.execution_result
        )


def test_audit_log_requires_guardrail_result():
    """
    The guardrail outcome is required to show whether the LLM's
    proposed action was accepted or overridden.
    """

    audit_log = create_valid_audit_log()

    with pytest.raises(ValidationError):
        AuditLog(
            audit_id="audit_002",
            timestamp=audit_log.timestamp,
            event=audit_log.event,
            customer_history=audit_log.customer_history,
            retry_history=audit_log.retry_history,
            payment_method_status=audit_log.payment_method_status,
            proposed_decision=audit_log.proposed_decision,
            execution_result=audit_log.execution_result
        )


def test_audit_log_requires_execution_result():
    """
    The execution result is required to complete the trace of what
    actually happened after the final action was approved.
    """

    audit_log = create_valid_audit_log()

    with pytest.raises(ValidationError):
        AuditLog(
            audit_id="audit_002",
            timestamp=audit_log.timestamp,
            event=audit_log.event,
            customer_history=audit_log.customer_history,
            retry_history=audit_log.retry_history,
            payment_method_status=audit_log.payment_method_status,
            proposed_decision=audit_log.proposed_decision,
            guardrail_result=audit_log.guardrail_result
        )