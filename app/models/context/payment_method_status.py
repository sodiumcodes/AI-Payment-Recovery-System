from pydantic import BaseModel, Field, model_validator
from app.models.enums import PaymentMethodStatusType

class PaymentMethodStatus(BaseModel):
    """
    Represents the current status and retry availability of the payment method associated with a payment.
    This context helps the recovery agent determine whether another payment retry is technically allowed.
    """

    payment_id: str = Field(min_length=1)

    # Represents the current known state of the payment method.
    # Using an enum prevents arbitrary or inconsistent status values.
    status: PaymentMethodStatusType

    # Explicitly tells the agent whether another retry is allowed.
    
    # This is kept separate from status because retryability may depend on system policy and other conditions, not only the status value.
    can_retry: bool

    # Explains why another retry is not possible.
    
    # This should only contain a value when can_retry is False.
    reason_if_not_retryable: str | None = None

    @model_validator(mode="after")
    def validate_retryability(self):
        #Validates that retryability and its explanation are consistent.

        # If a retry is allowed, there should not be a reason claiming that the payment method cannot be retried.
        if (
            self.can_retry
            and self.reason_if_not_retryable is not None
        ):
            raise ValueError(
                "reason_if_not_retryable must be None when can_retry is True"
            )

        # If a retry is not allowed, the system should provide a reason so that the decision is explainable and useful to the agent.
        if (
            not self.can_retry
            and not self.reason_if_not_retryable
        ):
            raise ValueError(
                "reason_if_not_retryable is required when can_retry is False"
            )

        return self