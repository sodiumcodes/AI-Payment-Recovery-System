from pydantic import BaseModel

from app.models.context.customer_history import CustomerHistory
from app.models.context.retry_history import RetryHistory
from app.models.context.payment_method_status import PaymentMethodStatus
from app.models.events.payment_failed import PaymentFailedEvent
from app.models.evaluation.ground_truth import GroundTruth

class SyntheticCase(BaseModel):
    """
    Represents one complete synthetic payment recovery scenario.

    A case contains the failed payment event, all relevant context,
    and deterministic ground truth for later evaluation.
    """

    event: PaymentFailedEvent
    customer_history: CustomerHistory
    retry_history: RetryHistory
    payment_method_status: PaymentMethodStatus
    ground_truth: GroundTruth