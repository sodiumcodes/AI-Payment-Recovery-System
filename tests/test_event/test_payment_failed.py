from datetime import datetime
import pytest
from pydantic import ValidationError

from app.models.enums import FailureType
from app.models.events.payment_failed import PaymentFailedEvent


def test_valid_payment_failed_event():

    event = PaymentFailedEvent(
        event_id="evt_001",
        payment_id="pay_001",
        customer_id="cust_001",
        amount=100000,
        currency="INR",
        failure_type=FailureType.NETWORK_TIMEOUT,
        retry_count=1,
        total_failures=2,
        timestamp=datetime.now()
    )

    assert event.event_id == "evt_001"
    assert event.event_type == "payment_failed"
    assert event.amount == 100000
    assert event.failure_type == FailureType.NETWORK_TIMEOUT


def test_amount_must_be_positive():

    with pytest.raises(ValidationError):
        PaymentFailedEvent(
            event_id="evt_002",
            payment_id="pay_002",
            customer_id="cust_001",
            amount=0,
            currency="INR",
            failure_type=FailureType.NETWORK_TIMEOUT,
            retry_count=0,
            total_failures=1,
            timestamp=datetime.now()
        )


def test_retry_count_cannot_be_negative():

    with pytest.raises(ValidationError):
        PaymentFailedEvent(
            event_id="evt_003",
            payment_id="pay_003",
            customer_id="cust_001",
            amount=100000,
            currency="INR",
            failure_type=FailureType.NETWORK_TIMEOUT,
            retry_count=-1,
            total_failures=1,
            timestamp=datetime.now()
        )


def test_total_failures_must_be_at_least_one():

    with pytest.raises(ValidationError):
        PaymentFailedEvent(
            event_id="evt_004",
            payment_id="pay_004",
            customer_id="cust_001",
            amount=100000,
            currency="INR",
            failure_type=FailureType.NETWORK_TIMEOUT,
            retry_count=0,
            total_failures=0,
            timestamp=datetime.now()
        )


def test_total_failures_must_match_retry_count():

    with pytest.raises(ValidationError):
        PaymentFailedEvent(
            event_id="evt_005",
            payment_id="pay_005",
            customer_id="cust_001",
            amount=100000,
            currency="INR",
            failure_type=FailureType.NETWORK_TIMEOUT,
            retry_count=3,
            total_failures=2,
            timestamp=datetime.now()
        )


def test_invalid_failure_type_is_rejected():

    with pytest.raises(ValidationError):
        PaymentFailedEvent(
            event_id="evt_006",
            payment_id="pay_006",
            customer_id="cust_001",
            amount=100000,
            currency="INR",
            failure_type="random_error",
            retry_count=0,
            total_failures=1,
            timestamp=datetime.now()
        )


def test_invalid_event_type_is_rejected():

    with pytest.raises(ValidationError):
        PaymentFailedEvent(
            event_id="evt_007",
            event_type="checkout_abandoned",
            payment_id="pay_007",
            customer_id="cust_001",
            amount=100000,
            currency="INR",
            failure_type=FailureType.NETWORK_TIMEOUT,
            retry_count=0,
            total_failures=1,
            timestamp=datetime.now()
        )