import pytest
from pydantic import ValidationError
from app.models.context.payment_method_status import PaymentMethodStatus
from app.models.enums import PaymentMethodStatusType

def test_valid_retryable_payment_method():
    #A valid payment method that can be retried should be created successfully without a non-retryable reason.
    
    payment_method = PaymentMethodStatus(
        payment_id="pay_001",
        status=PaymentMethodStatusType.ACTIVE,
        can_retry=True,
        reason_if_not_retryable=None
    )

    assert payment_method.payment_id == "pay_001"
    assert payment_method.status == PaymentMethodStatusType.ACTIVE
    assert payment_method.can_retry is True
    assert payment_method.reason_if_not_retryable is None


def test_valid_non_retryable_payment_method():
    #A payment method that cannot be retried must include a reason explaining why another retry is not possible.


    payment_method = PaymentMethodStatus(
        payment_id="pay_001",
        status=PaymentMethodStatusType.EXPIRED,
        can_retry=False,
        reason_if_not_retryable="Payment method has expired"
    )

    assert payment_method.can_retry is False
    assert (
        payment_method.reason_if_not_retryable
        == "Payment method has expired"
    )


def test_payment_id_cannot_be_empty():
    #Every payment method status must belong to a specific payment.

    with pytest.raises(ValidationError):
        PaymentMethodStatus(
            payment_id="",
            status=PaymentMethodStatusType.ACTIVE,
            can_retry=True
        )


def test_invalid_payment_method_status_is_rejected():
    """
    The status must be one of the predefined enum values.
    Arbitrary strings should not be accepted.
    """

    with pytest.raises(ValidationError):
        PaymentMethodStatus(
            payment_id="pay_001",
            status="unknown_status",
            can_retry=True
        )


def test_retryable_payment_method_cannot_have_non_retryable_reason():
    #If can_retry is True, there should not be a reason claiming that the payment method cannot be retried.
    
    with pytest.raises(ValidationError):
        PaymentMethodStatus(
            payment_id="pay_001",
            status=PaymentMethodStatusType.ACTIVE,
            can_retry=True,
            reason_if_not_retryable="Payment method is blocked"
        )


def test_non_retryable_payment_method_requires_reason():
    #If can_retry is False, a reason must be provided so the decision remains explainable.
    
    with pytest.raises(ValidationError):
        PaymentMethodStatus(
            payment_id="pay_001",
            status=PaymentMethodStatusType.EXPIRED,
            can_retry=False,
            reason_if_not_retryable=None
        )


def test_non_retryable_payment_method_cannot_have_empty_reason():
    #An empty string is not a meaningful explanation for why the payment method cannot be retried.

    with pytest.raises(ValidationError):
        PaymentMethodStatus(
            payment_id="pay_001",
            status=PaymentMethodStatusType.BLOCKED,
            can_retry=False,
            reason_if_not_retryable=""
        )