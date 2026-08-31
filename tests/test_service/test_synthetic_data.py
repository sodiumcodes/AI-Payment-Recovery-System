import pytest
from pydantic import ValidationError

from app.models.enums import RecoveryAction, FailureType, PaymentMethodStatusType
from app.services.synthetic_data import SyntheticPaymentGenerator
from app.models.evaluation.synthetic_case import SyntheticCase

def test_generate_dataset_returns_exact_count():
    """Verify that dataset generation produces exactly the requested number of cases."""
    generator = SyntheticPaymentGenerator(seed=42)
    count = 100
    dataset = generator.generate_dataset(count)
    assert len(dataset) == count
    assert all(isinstance(case, SyntheticCase) for case in dataset)


def test_generate_event_compatibility():
    """Verify backward compatibility of generate_event method."""
    generator = SyntheticPaymentGenerator(seed=42)
    dataset = generator.generate_event(5)
    assert len(dataset) == 5


def test_invalid_count_raises_value_error():
    """Verify ValueError is raised when count <= 0."""
    generator = SyntheticPaymentGenerator(seed=42)
    with pytest.raises(ValueError, match="count must be greater than 0"):
        generator.generate_dataset(0)

    with pytest.raises(ValueError, match="count must be greater than 0"):
        generator.generate_dataset(-10)


def test_deterministic_generation_with_seed():
    """Verify that using the same seed produces identical dataset cases."""
    gen1 = SyntheticPaymentGenerator(seed=12345)
    gen2 = SyntheticPaymentGenerator(seed=12345)

    dataset1 = gen1.generate_dataset(20)
    dataset2 = gen2.generate_dataset(20)

    for case1, case2 in zip(dataset1, dataset2):
        assert case1.event.event_id == case2.event.event_id
        assert case1.event.payment_id == case2.event.payment_id
        assert case1.event.customer_id == case2.event.customer_id
        assert case1.event.amount == case2.event.amount
        assert case1.event.failure_type == case2.event.failure_type
        assert case1.ground_truth.expected_action == case2.ground_truth.expected_action
        assert case1.ground_truth.expected_recovery_probability == case2.ground_truth.expected_recovery_probability
        assert case1.ground_truth.reason == case2.ground_truth.reason


def test_data_consistency_ids_match_across_objects():
    """
    Verify customer IDs and payment IDs match across all related context objects:
    - event.customer_id == customer_history.customer_id
    - event.payment_id == retry_history.payment_id == payment_method_status.payment_id
    """
    generator = SyntheticPaymentGenerator(seed=42)
    dataset = generator.generate_dataset(50)

    for case in dataset:
        # Customer ID alignment
        assert case.event.customer_id == case.customer_history.customer_id

        # Payment ID alignment
        assert case.event.payment_id == case.retry_history.payment_id
        assert case.event.payment_id == case.payment_method_status.payment_id


def test_model_validation_constraints():
    """Verify all generated objects satisfy specific model validation constraints."""
    generator = SyntheticPaymentGenerator(seed=42)
    dataset = generator.generate_dataset(100)

    for case in dataset:
        # Event failure counts constraint
        assert case.event.total_failures >= case.event.retry_count + 1

        # Retry history constraints
        assert case.retry_history.successful_retries + case.retry_history.failed_retries <= case.retry_history.total_attempts
        if case.retry_history.total_attempts == 0:
            assert case.retry_history.last_retry_at is None
        else:
            assert case.retry_history.last_retry_at is not None

        # Payment method status constraints
        if case.payment_method_status.can_retry:
            assert case.payment_method_status.reason_if_not_retryable is None
        else:
            assert case.payment_method_status.reason_if_not_retryable is not None
            assert len(case.payment_method_status.reason_if_not_retryable) > 0


def test_ground_truth_validity():
    """Verify ground truth output validity across generated cases."""
    generator = SyntheticPaymentGenerator(seed=42)
    dataset = generator.generate_dataset(100)

    for case in dataset:
        gt = case.ground_truth
        assert isinstance(gt.expected_action, RecoveryAction)
        assert isinstance(gt.expected_recoverable, bool)
        assert 0.0 <= gt.expected_recovery_probability <= 1.0
        assert isinstance(gt.reason, str)
        assert len(gt.reason.strip()) > 0


def test_scenario_diversity_and_edge_cases():
    """Verify dataset contains a rich distribution of scenarios and edge cases."""
    generator = SyntheticPaymentGenerator(seed=100)
    dataset = generator.generate_dataset(200)

    actions = {case.ground_truth.expected_action for case in dataset}
    failure_types = {case.event.failure_type for case in dataset}
    statuses = {case.payment_method_status.status for case in dataset}

    # All RecoveryAction enums represented
    assert RecoveryAction.RETRY in actions
    assert RecoveryAction.NOTIFY in actions
    assert RecoveryAction.ESCALATE in actions
    assert RecoveryAction.STOP in actions

    # Failure types represented
    assert FailureType.NETWORK_TIMEOUT in failure_types
    assert FailureType.INSUFFICIENT_FUNDS in failure_types
    assert FailureType.PERSISTENT_FAILURE in failure_types
    assert FailureType.PAYMENT_METHOD_ERROR in failure_types

    # Payment method status types represented
    assert PaymentMethodStatusType.ACTIVE in statuses
    assert PaymentMethodStatusType.EXPIRED in statuses
    assert PaymentMethodStatusType.BLOCKED in statuses

    # Verify edge cases: new customers (0 past successful payments) and high value payments (> 50,000)
    has_new_customer = any(c.customer_history.total_successful_payments == 0 for c in dataset)
    has_high_value = any(c.event.amount >= 50_000 for c in dataset)
    has_no_retries = any(c.retry_history.total_attempts == 0 for c in dataset)
    has_multiple_retries = any(c.retry_history.total_attempts >= 3 for c in dataset)

    assert has_new_customer
    assert has_high_value
    assert has_no_retries
    assert has_multiple_retries
