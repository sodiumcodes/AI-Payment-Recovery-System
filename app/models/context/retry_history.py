from datetime import datetime
from pydantic import BaseModel, Field, model_validator

class RetryHistory(BaseModel):
   
    # Identifies the payment this retry history belongs to.
    payment_id: str = Field(min_length=1)

    # Total number of retry attempts made for this payment.
    total_attempts: int = Field(ge=0)

    # Number of retry attempts that resulted in a successful outcome.
    successful_retries: int = Field(ge=0)

    # Number of retry attempts that resulted in failure.
    failed_retries: int = Field(ge=0)

    # Timestamp of the most recent retry attempt.
    # This is None when no retries have been attempted yet.
    last_retry_at: datetime | None = None

    @model_validator(mode="after")
    def validate_retry_history(self):
    
        # The number of successful and failed retries cannot exceed the total number of retry attempts.
        
        # We use <= rather than == because some attempts may have
        # unresolved outcomes, such as pending or timed-out retries.
        if (
            self.successful_retries + self.failed_retries
            > self.total_attempts
        ):
            raise ValueError(
                "successful_retries + failed_retries "
                "cannot exceed total_attempts"
            )

        # If no retries have been attempted, there cannot be a timestamp representing the most recent retry.
        if (
            self.total_attempts == 0
            and self.last_retry_at is not None
        ):
            raise ValueError(
                "last_retry_at must be None when total_attempts is 0"
            )

        # If one or more retries have been attempted, we require the timestamp of the most recent retry so the agent can reason about retry timing.
        if (
            self.total_attempts > 0
            and self.last_retry_at is None
        ):
            raise ValueError(
                "last_retry_at is required when retries have been attempted"
            )
        
        return self