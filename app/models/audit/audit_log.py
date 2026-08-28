from datetime import datetime
from pydantic import BaseModel, Field
from app.models.context.customer_history import CustomerHistory
from app.models.context.payment_method_status import PaymentMethodStatus
from app.models.context.retry_history import RetryHistory
from app.models.decisions.recovery_decision import RecoveryDecision
from app.models.events.payment_failed import PaymentFailedEvent
from app.models.execution.execution_result import ExecutionResult
from app.models.guardrails.guardrail_result import GuardrailResult


class AuditLog(BaseModel):
    """
    Represents a complete, traceable record of a payment recovery workflow.

    The audit log captures the original event, the context provided to
    the agent, the decision proposed by the LLM, the guardrail outcome,
    and the final execution result.
    """

    # Unique identifier for this audit record.
    audit_id: str = Field(min_length=1)

    # Records when this recovery workflow was logged.
    # This is separate from the original event timestamp.
    timestamp: datetime

    # The event that triggered the recovery workflow.
    event: PaymentFailedEvent

    # Historical information about the customer provided to the agent.
    customer_history: CustomerHistory

    # Historical information about retry attempts for this payment.
    retry_history: RetryHistory

    # Current retryability and status of the payment method.
    payment_method_status: PaymentMethodStatus

    # The structured recovery decision proposed by the LLM.
    proposed_decision: RecoveryDecision

    # The result after deterministic guardrails evaluated the proposal.
    guardrail_result: GuardrailResult

    # The actual result of executing the final approved action.
    execution_result: ExecutionResult