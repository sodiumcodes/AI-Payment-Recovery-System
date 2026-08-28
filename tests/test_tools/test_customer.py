from datetime import datetime
import pytest
from pydantic import ValidationError

from app.models.context.customer_history import CustomerHistory

def test_valid_customer_history():

    history = CustomerHistory(
        customer_id="cust_001",
        total_successful_payments=10,
        total_failed_payments=3,
        previous_recoveries=2,
        last_successful_payment_at=datetime.now()
    )

    assert history.customer_id == "cust_001"
    assert history.total_successful_payments == 10
    assert history.total_failed_payments == 3
    assert history.previous_recoveries == 2


def test_customer_id_cannot_be_empty():

    with pytest.raises(ValidationError):
        CustomerHistory(
            customer_id="",
            total_successful_payments=10,
            total_failed_payments=3,
            previous_recoveries=2
        )


def test_successful_payments_cannot_be_negative():

    with pytest.raises(ValidationError):
        CustomerHistory(
            customer_id="cust_001",
            total_successful_payments=-1,
            total_failed_payments=3,
            previous_recoveries=2
        )


def test_failed_payments_cannot_be_negative():

    with pytest.raises(ValidationError):
        CustomerHistory(
            customer_id="cust_001",
            total_successful_payments=10,
            total_failed_payments=-1,
            previous_recoveries=2
        )


def test_previous_recoveries_cannot_be_negative():

    with pytest.raises(ValidationError):
        CustomerHistory(
            customer_id="cust_001",
            total_successful_payments=10,
            total_failed_payments=3,
            previous_recoveries=-1
        )


def test_last_successful_payment_can_be_none():

    history = CustomerHistory(
        customer_id="cust_001",
        total_successful_payments=0,
        total_failed_payments=2,
        previous_recoveries=0,
        last_successful_payment_at=None
    )

    assert history.last_successful_payment_at is None