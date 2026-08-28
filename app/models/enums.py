# system contract decision : The recovery actions and failure types are part of the system's controlled vocabulary. They are defined once and reused everywhere instead of being represented by arbitrary strings.

from enum import Enum

class RecoveryAction(str, Enum):
    RETRY = "retry"
    NOTIFY = "notify"
    ESCALATE = "escalate"
    STOP = "stop"

class FailureType(str, Enum):
    NETWORK_TIMEOUT = "network_timeout"
    INSUFFICIENT_FUNDS = "insufficient_funds"
    PERSISTENT_FAILURE = "persistent_failure"
    PAYMENT_METHOD_ERROR = "payment_method_error"