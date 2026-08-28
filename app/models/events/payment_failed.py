from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, model_validator
from app.models.enums import FailureType

class PaymentFailedEvent(BaseModel):
    # Event identity
    event_id: str = Field(
        min_length=1,
        description= "Unique identifier for this event."
    )

    event_type: Literal["payment_failed"] = "payment_failed"

    # Payment identity
    payment_id: str = Field(
        min_length=1,
        description= "Identifier of the payment that failed."
    )

    customer_id: str = Field(
        min_length=1,
        description="Identifier of the customer associated with the payment."
    )

    # Payment details
    amount: int = Field(
        gt=0,
        description="Payment amount in the smallest currency unit."
    )

    currency: str = Field(
        min_length=3,
        max_length=3,
        description="Three-letter currency code."
    )

    # Failure information
    failure_type: FailureType

    retry_count: int = Field(
        ge=0,
        description="Number of retry attempts already made."
    )

    total_failures: int = Field(
        ge=1,
        description= "Total failed attempts, including the current failure."
    )

    # Event timing
    timestamp: datetime

    @model_validator(mode = "after")
    def validate_failure_counts(self):
        if self.total_failures < self.retry_count + 1:
            raise ValueError(
                "total_failures must be at least retry_count + 1."
            )

        return self