from datetime import datetime, timedelta, timezone
from random import Random
from uuid import uuid4

from app.models.enums import (
    FailureType,
    PaymentMethodStatusType,
    RecoveryAction,
)
from app.models.evaluation.synthetic_case import SyntheticCase
from app.models.context.customer_history import CustomerHistory
from app.models.context.retry_history import RetryHistory
from app.models.context.payment_method_status import PaymentMethodStatus
from app.models.events.payment_failed import PaymentFailedEvent
from app.models.evaluation.ground_truth import GroundTruth

class SyntheticPaymentGenerator:
    """
    Generates realistic synthetic payment failure scenarios.

    The generator does not create completely random independent fields.
    Instead, it creates correlated scenarios where customer history,
    failure type, retry history, payment method status, and ground truth
    logically relate to one another.
    """

    def __init__(self, seed: int | None = None):
        self.random = Random(seed)

    def generate_dataset(
        self,
        count: int = 100,
    ) -> list[SyntheticCase]:
        if count <= 0:
            raise ValueError("count must be greater than 0")

        dataset = []
        for _ in range(count):
            scenario = self._choose_scenario()
            case = self._generate_case(scenario=scenario)
            dataset.append(case)

        return dataset

    def generate_event(
        self,
        count: int = 1,
    ) -> list[SyntheticCase]:
        return self.generate_dataset(count)

    def _choose_scenario(self) -> str:
        """
        Controls the distribution of synthetic cases.

        We intentionally generate more common scenarios and fewer
        edge cases, rather than making every scenario equally likely.
        """
        scenarios = [
            "temporary_network_failure",
            "insufficient_funds",
            "repeated_failures",
            "expired_payment_method",
            "blocked_payment_method",
            "high_value_payment_failure",
            "new_customer",
            "loyal_customer",
        ]

        weights = [
            25,  # temporary network failure
            20,  # insufficient funds
            15,  # repeated failures
            10,  # expired payment method
            5,   # blocked payment method
            10,  # high-value failure
            10,  # new customer
            5,   # loyal customer
        ]

        return self.random.choices(
            scenarios,
            weights=weights,
            k=1,
        )[0]

    def _generate_case(
        self,
        scenario: str,
    ) -> SyntheticCase:
        customer_id = self._generate_customer_id()
        payment_id = self._generate_payment_id()
        event_id = f"evt_{self.random.getrandbits(48):012x}"

        now = datetime.now(timezone.utc)

        if scenario == "temporary_network_failure":
            customer_history = CustomerHistory(
                customer_id=customer_id,
                total_successful_payments=self.random.randint(5, 50),
                total_failed_payments=self.random.randint(0, 3),
                previous_recoveries=self.random.randint(0, 2),
                last_successful_payment_at=(
                    now - timedelta(days=self.random.randint(1, 30))
                ),
            )

            retry_count = self.random.randint(0, 1)

            retry_history = self._create_retry_history(
                payment_id=payment_id,
                retry_count=retry_count,
                now=now,
            )

            payment_method_status = PaymentMethodStatus(
                payment_id=payment_id,
                status=PaymentMethodStatusType.ACTIVE,
                can_retry=True,
                reason_if_not_retryable=None,
            )

            event = self._create_event(
                event_id=event_id,
                payment_id=payment_id,
                customer_id=customer_id,
                amount=self._generate_normal_amount(),
                failure_type=FailureType.NETWORK_TIMEOUT,
                retry_count=retry_count,
                timestamp=now,
            )

            ground_truth = GroundTruth(
                expected_action=RecoveryAction.RETRY,
                expected_recoverable=True,
                expected_recovery_probability=0.90,
                reason=(
                    "The payment failed due to a temporary network "
                    "timeout and the payment method remains active "
                    "and retryable."
                ),
            )

        elif scenario == "insufficient_funds":
            successful_payments = self.random.randint(1, 25)
            failed_payments = self.random.randint(1, 5)

            customer_history = CustomerHistory(
                customer_id=customer_id,
                total_successful_payments=successful_payments,
                total_failed_payments=failed_payments,
                previous_recoveries=self.random.randint(
                    0, min(failed_payments, 2)
                ),
                last_successful_payment_at=(
                    now - timedelta(days=self.random.randint(1, 60))
                ),
            )

            retry_count = self.random.randint(0, 2)

            retry_history = self._create_retry_history(
                payment_id=payment_id,
                retry_count=retry_count,
                now=now,
            )

            payment_method_status = PaymentMethodStatus(
                payment_id=payment_id,
                status=PaymentMethodStatusType.ACTIVE,
                can_retry=True,
                reason_if_not_retryable=None,
            )

            event = self._create_event(
                event_id=event_id,
                payment_id=payment_id,
                customer_id=customer_id,
                amount=self._generate_normal_amount(),
                failure_type=FailureType.INSUFFICIENT_FUNDS,
                retry_count=retry_count,
                timestamp=now,
            )

            ground_truth = GroundTruth(
                expected_action=RecoveryAction.RETRY,
                expected_recoverable=True,
                expected_recovery_probability=0.65,
                reason=(
                    "The payment method is active and insufficient "
                    "funds may be a temporary condition, so a delayed "
                    "retry is reasonable."
                ),
            )

        elif scenario == "repeated_failures":
            failed_payments = self.random.randint(5, 15)

            customer_history = CustomerHistory(
                customer_id=customer_id,
                total_successful_payments=self.random.randint(0, 10),
                total_failed_payments=failed_payments,
                previous_recoveries=self.random.randint(
                    0, min(2, failed_payments)
                ),
                last_successful_payment_at=(
                    now - timedelta(days=self.random.randint(30, 180))
                ),
            )

            retry_count = self.random.randint(3, 5)

            retry_history = self._create_retry_history(
                payment_id=payment_id,
                retry_count=retry_count,
                now=now,
            )

            payment_method_status = PaymentMethodStatus(
                payment_id=payment_id,
                status=PaymentMethodStatusType.ACTIVE,
                can_retry=True,
                reason_if_not_retryable=None,
            )

            event = self._create_event(
                event_id=event_id,
                payment_id=payment_id,
                customer_id=customer_id,
                amount=self._generate_normal_amount(),
                failure_type=FailureType.PERSISTENT_FAILURE,
                retry_count=retry_count,
                timestamp=now,
            )

            ground_truth = GroundTruth(
                expected_action=RecoveryAction.NOTIFY,
                expected_recoverable=False,
                expected_recovery_probability=0.25,
                reason=(
                    "Multiple retry attempts have already failed, "
                    "so another automatic retry has a low expected value."
                ),
            )

        elif scenario == "expired_payment_method":
            failed_payments = self.random.randint(1, 8)

            customer_history = CustomerHistory(
                customer_id=customer_id,
                total_successful_payments=self.random.randint(1, 30),
                total_failed_payments=failed_payments,
                previous_recoveries=self.random.randint(
                    0, min(3, failed_payments)
                ),
                last_successful_payment_at=(
                    now - timedelta(days=self.random.randint(10, 120))
                ),
            )

            retry_count = self.random.randint(0, 2)

            retry_history = self._create_retry_history(
                payment_id=payment_id,
                retry_count=retry_count,
                now=now,
            )

            payment_method_status = PaymentMethodStatus(
                payment_id=payment_id,
                status=PaymentMethodStatusType.EXPIRED,
                can_retry=False,
                reason_if_not_retryable="The payment method has expired.",
            )

            event = self._create_event(
                event_id=event_id,
                payment_id=payment_id,
                customer_id=customer_id,
                amount=self._generate_normal_amount(),
                failure_type=FailureType.PAYMENT_METHOD_ERROR,
                retry_count=retry_count,
                timestamp=now,
            )

            ground_truth = GroundTruth(
                expected_action=RecoveryAction.NOTIFY,
                expected_recoverable=False,
                expected_recovery_probability=0.15,
                reason=(
                    "The payment method is expired and cannot be "
                    "automatically retried. The customer needs to "
                    "update their payment method."
                ),
            )

        elif scenario == "blocked_payment_method":
            failed_payments = self.random.randint(2, 10)

            customer_history = CustomerHistory(
                customer_id=customer_id,
                total_successful_payments=self.random.randint(0, 15),
                total_failed_payments=failed_payments,
                previous_recoveries=self.random.randint(
                    0, min(2, failed_payments)
                ),
                last_successful_payment_at=(
                    now - timedelta(days=self.random.randint(30, 365))
                ),
            )

            retry_count = self.random.randint(1, 4)

            retry_history = self._create_retry_history(
                payment_id=payment_id,
                retry_count=retry_count,
                now=now,
            )

            payment_method_status = PaymentMethodStatus(
                payment_id=payment_id,
                status=PaymentMethodStatusType.BLOCKED,
                can_retry=False,
                reason_if_not_retryable="The payment method is blocked.",
            )

            event = self._create_event(
                event_id=event_id,
                payment_id=payment_id,
                customer_id=customer_id,
                amount=self._generate_normal_amount(),
                failure_type=FailureType.PAYMENT_METHOD_ERROR,
                retry_count=retry_count,
                timestamp=now,
            )

            ground_truth = GroundTruth(
                expected_action=RecoveryAction.STOP,
                expected_recoverable=False,
                expected_recovery_probability=0.05,
                reason=(
                    "The payment method is blocked and cannot be "
                    "retried automatically."
                ),
            )

        elif scenario == "high_value_payment_failure":
            customer_history = CustomerHistory(
                customer_id=customer_id,
                total_successful_payments=self.random.randint(10, 100),
                total_failed_payments=self.random.randint(0, 5),
                previous_recoveries=self.random.randint(0, 3),
                last_successful_payment_at=(
                    now - timedelta(days=self.random.randint(1, 20))
                ),
            )

            retry_count = self.random.randint(1, 3)

            retry_history = self._create_retry_history(
                payment_id=payment_id,
                retry_count=retry_count,
                now=now,
            )

            payment_method_status = PaymentMethodStatus(
                payment_id=payment_id,
                status=PaymentMethodStatusType.ACTIVE,
                can_retry=True,
                reason_if_not_retryable=None,
            )

            event = self._create_event(
                event_id=event_id,
                payment_id=payment_id,
                customer_id=customer_id,
                amount=self.random.randint(50_000, 500_000),
                failure_type=FailureType.PERSISTENT_FAILURE,
                retry_count=retry_count,
                timestamp=now,
            )

            ground_truth = GroundTruth(
                expected_action=RecoveryAction.ESCALATE,
                expected_recoverable=True,
                expected_recovery_probability=0.50,
                reason=(
                    "This is a high-value payment with repeated failure "
                    "signals, so the case should be escalated rather "
                    "than repeatedly retried automatically."
                ),
            )

        elif scenario == "new_customer":
            customer_history = CustomerHistory(
                customer_id=customer_id,
                total_successful_payments=0,
                total_failed_payments=0,
                previous_recoveries=0,
                last_successful_payment_at=None,
            )

            retry_count = 0

            retry_history = self._create_retry_history(
                payment_id=payment_id,
                retry_count=retry_count,
                now=now,
            )

            payment_method_status = PaymentMethodStatus(
                payment_id=payment_id,
                status=PaymentMethodStatusType.ACTIVE,
                can_retry=True,
                reason_if_not_retryable=None,
            )

            event = self._create_event(
                event_id=event_id,
                payment_id=payment_id,
                customer_id=customer_id,
                amount=self._generate_normal_amount(),
                failure_type=FailureType.NETWORK_TIMEOUT,
                retry_count=retry_count,
                timestamp=now,
            )

            ground_truth = GroundTruth(
                expected_action=RecoveryAction.RETRY,
                expected_recoverable=True,
                expected_recovery_probability=0.70,
                reason=(
                    "There is no negative payment history and the "
                    "payment method is active, so one controlled retry "
                    "is reasonable."
                ),
            )

        elif scenario == "loyal_customer":
            failed_payments = self.random.randint(0, 3)

            customer_history = CustomerHistory(
                customer_id=customer_id,
                total_successful_payments=self.random.randint(50, 200),
                total_failed_payments=failed_payments,
                previous_recoveries=self.random.randint(0, failed_payments),
                last_successful_payment_at=(
                    now - timedelta(days=self.random.randint(1, 7))
                ),
            )

            retry_count = self.random.randint(0, 1)

            retry_history = self._create_retry_history(
                payment_id=payment_id,
                retry_count=retry_count,
                now=now,
            )

            payment_method_status = PaymentMethodStatus(
                payment_id=payment_id,
                status=PaymentMethodStatusType.ACTIVE,
                can_retry=True,
                reason_if_not_retryable=None,
            )

            event = self._create_event(
                event_id=event_id,
                payment_id=payment_id,
                customer_id=customer_id,
                amount=self._generate_normal_amount(),
                failure_type=self.random.choice(
                    [
                        FailureType.NETWORK_TIMEOUT,
                        FailureType.INSUFFICIENT_FUNDS,
                    ]
                ),
                retry_count=retry_count,
                timestamp=now,
            )

            ground_truth = GroundTruth(
                expected_action=RecoveryAction.RETRY,
                expected_recoverable=True,
                expected_recovery_probability=0.85,
                reason=(
                    "The customer has a strong successful payment "
                    "history and the payment method remains active."
                ),
            )

        else:
            raise ValueError(f"Unknown scenario: {scenario}")

        return SyntheticCase(
            event=event,
            customer_history=customer_history,
            retry_history=retry_history,
            payment_method_status=payment_method_status,
            ground_truth=ground_truth,
        )

    def _create_event(
        self,
        event_id: str,
        payment_id: str,
        customer_id: str,
        amount: int,
        failure_type: FailureType,
        retry_count: int,
        timestamp: datetime,
    ) -> PaymentFailedEvent:
        return PaymentFailedEvent(
            event_id=event_id,
            payment_id=payment_id,
            customer_id=customer_id,
            amount=amount,
            currency="INR",
            failure_type=failure_type,
            retry_count=retry_count,
            total_failures=retry_count + 1,
            timestamp=timestamp,
        )

    def _create_retry_history(
        self,
        payment_id: str,
        retry_count: int,
        now: datetime,
    ) -> RetryHistory:
        if retry_count == 0:
            return RetryHistory(
                payment_id=payment_id,
                total_attempts=0,
                successful_retries=0,
                failed_retries=0,
                last_retry_at=None,
            )

        return RetryHistory(
            payment_id=payment_id,
            total_attempts=retry_count,
            successful_retries=0,
            failed_retries=retry_count,
            last_retry_at=(
                now - timedelta(minutes=self.random.randint(5, 1440))
            ),
        )

    def _generate_customer_id(self) -> str:
        return f"cus_{self.random.randint(10000, 99999)}"

    def _generate_payment_id(self) -> str:
        return f"pay_{self.random.getrandbits(48):012x}"

    def _generate_normal_amount(self) -> int:
        """
        Generates an amount in the smallest currency unit.
        """
        return self.random.randint(1_000, 100_000)
