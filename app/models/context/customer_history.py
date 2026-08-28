from datetime import datetime
from pydantic import BaseModel, Field

class CustomerHistory(BaseModel):

    # Identifies which customer's historical data this context belongs to.
    customer_id: str = Field(
        min_length=1,
        description="Identifier of the customer whose history is being returned."
    )

    # Shows how often this customer has successfully completed payments.
    total_successful_payments: int = Field(
        ge=0,
        description="Total number of successful payments made by the customer."
    )

    # Helps identify whether the customer has a history of repeated payment failures.
    total_failed_payments: int = Field(
        ge=0,
        description="Total number of failed payments associated with the customer."
    )

    # Shows whether previous failed payments were successfully recovered.
    previous_recoveries: int = Field(
        ge=0,
        description=(
            "Number of previous failed payments that were successfully recovered."
        )
    )

    # Provides recency information about the customer's last successful payment.
    last_successful_payment_at: datetime | None = Field(
        default=None,
        description="Timestamp of the customer's most recent successful payment."
    )