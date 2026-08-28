# AI-Powered Payment Recovery Agent

An AI-powered payment recovery system that analyzes failed payment events, gathers relevant customer and payment context, proposes a recovery action using an LLM, applies deterministic guardrails, executes the approved action, and records the complete workflow for auditing and evaluation.

---

## Overview

When a payment fails, the system should not blindly retry every transaction or rely entirely on an LLM to decide what happens next.

Different failures may require different actions.

For example:

* A temporary network failure may be retryable.
* A payment method may no longer be retryable.
* Multiple failed attempts may require escalation.
* Continuing recovery attempts may no longer be useful.

This project is designed as a structured recovery pipeline where the LLM acts as a **decision-making component**, but deterministic system rules remain responsible for enforcing safety and business constraints.

The core principle is:

```text
LLM proposes.
Guardrails decide what is allowed.
The executor performs the approved action.
The audit system records everything.
```

---

# System Architecture

The complete recovery workflow is:

```text
Payment Failure
      ↓
PaymentFailedEvent
      ↓
Collect Agent Context
      ├── CustomerHistory
      ├── RetryHistory
      └── PaymentMethodStatus
      ↓
LLM / Agent
      ↓
RecoveryDecision
      ↓
Deterministic Guardrails
      ↓
GuardrailResult
      ↓
Executor
      ↓
ExecutionResult
      ↓
AuditLog
```

Each stage has a specific responsibility and communicates through validated data contracts.

---

# Project Scope

The initial version of the system focuses on one event:

```text
payment_failed
```

The system receives a failed payment event and determines the most appropriate recovery action.

Possible future events may include:

```text
checkout_abandoned
subscription_lapsed
payment_pending
```

However, the first version intentionally focuses on a single event type to keep the system boundary clear and make the recovery workflow easier to design, test, evaluate, and explain.

---

# Core Design Principles

## 1. Structured contracts

Core workflow data is represented using typed Pydantic models.

Instead of passing arbitrary dictionaries between components:

```python
data = {
    "action": "maybe retry later",
    "confidence": "high"
}
```

the system uses validated contracts with controlled fields and enums.

This ensures that invalid or contradictory data is rejected early.

---

## 2. Bounded decision space

The LLM does not generate arbitrary actions.

It must choose from a predefined set of recovery actions represented by `RecoveryAction`.

This prevents ambiguous decisions such as:

```text
"Try something else"
"Maybe contact the customer"
"Wait and see"
```

The decision space is controlled and predictable.

---

## 3. The LLM is not the final authority

The LLM produces a proposed recovery decision.

That decision passes through deterministic guardrails before execution.

```text
LLM Proposal
      ↓
Guardrail Evaluation
      ↓
Approved or Overridden Action
```

This prevents the model from directly controlling payment recovery behavior.

---

## 4. Decision and execution are separate

A correct decision does not guarantee successful execution.

For example:

```text
LLM proposes RETRY
        ↓
Guardrails approve RETRY
        ↓
Executor attempts retry
        ↓
Execution fails
```

The system records the decision and execution outcome separately.

---

## 5. Every workflow should be traceable

The system records:

* what event occurred
* what context was available
* what the LLM proposed
* whether guardrails changed the decision
* what action was executed
* what the execution result was

This makes the system explainable and auditable.

---

# Project Structure

```text
app/
├── models/
│   ├── audit/
│   ├── context/
│   ├── decisions/
│   ├── events/
│   ├── execution/
│   ├── guardrails/
│   ├── __init__.py
│   └── enums.py
│
├── tools/
├── agent/
├── guardrails/
├── executor/
├── database/
├── services/
└── main.py
```

The project separates **data contracts** from **system behavior**.

## `models/`

Contains validated data contracts.

Examples:

```text
PaymentFailedEvent
RecoveryDecision
GuardrailResult
ExecutionResult
AuditLog
```

These models define what valid data looks like.

---

## `tools/`

Will contain the logic used to retrieve information required by the agent.

Examples:

```text
get_customer_history
get_retry_history
get_payment_method_status
```

---

## `agent/`

Will contain the LLM orchestration and decision-making logic.

The agent will receive validated event and context data and produce a `RecoveryDecision`.

---

## `guardrails/`

Will contain deterministic rules that evaluate the LLM's proposed decision.

Examples include:

* maximum retry limits
* payment method restrictions
* escalation requirements
* stopping conditions

---

## `executor/`

Will contain the logic responsible for performing approved actions.

Examples:

```text
retry payment
send notification
escalate to human
stop recovery
```

---

## `database/`

Will contain persistence logic.

MongoDB is the planned database for storing workflow and audit data.

---

## `services/`

Will contain higher-level application services responsible for coordinating multiple components.

---

# Shared Enums

The project uses enums to restrict important states and actions.

## `RecoveryAction`

Represents the fixed set of recovery actions available to the system.

The agent must choose from predefined actions rather than generating arbitrary text.

Examples include:

```text
RETRY
NOTIFY
ESCALATE
STOP
```

---

## `FailureType`

Represents the type of payment failure.

This gives the system structured information about why a payment failed.

For example:

```text
NETWORK_TIMEOUT
PERSISTENT_FAILURE
```

---

## `PaymentMethodStatusType`

Represents the current state of the payment method.

This helps determine whether another recovery attempt is technically possible.

---

## `ExecutionStatus`

Represents the outcome of an execution attempt.

```text
EXECUTED
FAILED
```

Using enums prevents inconsistent values such as:

```text
success
successful
done
worked
```

from representing the same state.

---

# Event Contract

## `PaymentFailedEvent`

**Location:**

```text
app/models/events/payment_failed.py
```

This is the entry point into the recovery workflow.

It represents the event that triggered the agent.

### Fields

```text
event_id
event_type
payment_id
customer_id
amount
currency
failure_type
retry_count
total_failures
timestamp
```

### Responsibility

The model answers:

> What happened when the payment failure entered the system?

---

## Validation

The model includes:

* field validation
* Pydantic validation
* cross-field validation

An important relationship exists between:

```text
retry_count
total_failures
```

The system requires:

```text
total_failures >= retry_count + 1
```

For example:

```text
Initial payment attempt → failed
Retry attempt #1 → failed
```

Therefore:

```text
retry_count = 1
total_failures = 2
```

This prevents logically inconsistent event data from entering the recovery workflow.

---

# Agent Context

The payment event alone is not enough for the agent to make an informed decision.

The system provides structured context through three contracts.

```text
Agent Context
├── CustomerHistory
├── RetryHistory
└── PaymentMethodStatus
```

These models are located in:

```text
app/models/context/
```

---

## `CustomerHistory`

**Location:**

```text
app/models/context/customer_history.py
```

Represents historical information about the customer.

### Fields

```text
customer_id
total_successful_payments
total_failed_payments
previous_recoveries
last_successful_payment_at
```

### Purpose

This context helps the agent understand the customer's historical payment behavior.

For example, a customer with many successful payments may represent a different recovery situation from one with repeated failures.

### Validation

The model validates:

* customer ID cannot be empty
* successful payment count cannot be negative
* failed payment count cannot be negative
* previous recovery count cannot be negative
* `last_successful_payment_at` may be `None`

---

## `RetryHistory`

**Location:**

```text
app/models/context/retry_history.py
```

Represents retry information for the relevant payment.

It answers questions such as:

```text
How many retries were attempted?
What happened during previous retries?
When was the last retry?
```

This is intentionally separate from customer history.

```text
CustomerHistory
      ↓
Long-term customer behavior

RetryHistory
      ↓
Recovery behavior for the current payment
```

---

## `PaymentMethodStatus`

**Location:**

```text
app/models/context/payment_method_status.py
```

Represents whether another recovery attempt is technically possible.

Important concepts include:

```text
status
can_retry
reason_if_not_retryable
```

The model prevents contradictory states.

For example:

```text
can_retry = True
reason_if_not_retryable = "Payment method is unavailable"
```

is invalid.

Similarly:

```text
can_retry = False
reason_if_not_retryable = None
```

is invalid.

This ensures that the agent receives logically consistent context.

---

# Agent Decision Contract

## `RecoveryDecision`

**Location:**

```text
app/models/decisions/recovery_decision.py
```

Represents the structured decision proposed by the LLM.

### Fields

```text
action
retry_after_minutes
reason
confidence
```

The key word is **proposed**.

The LLM does not directly execute an action.

```text
LLM
 ↓
RecoveryDecision
 ↓
Guardrails
 ↓
Final Action
```

---

## Validation Rules

If:

```text
action = RETRY
```

then:

```text
retry_after_minutes
```

must be provided and must be valid.

For actions other than `RETRY`:

```text
retry_after_minutes = None
```

This prevents contradictory decisions such as:

```text
action = ESCALATE
retry_after_minutes = 30
```

The model also validates:

```text
reason cannot be empty

0.0 <= confidence <= 1.0
```

Model confidence is treated as metadata rather than authority.

```text
High confidence does not guarantee a correct decision.
```

The guardrails remain responsible for enforcing deterministic constraints.

---

# Guardrail Contract

## `GuardrailResult`

**Location:**

```text
app/models/guardrails/guardrail_result.py
```

This model records what happened when deterministic rules evaluated the LLM's proposed action.

### Fields

```text
original_action
final_action
was_overridden
override_reason
```

The model answers:

> What did the LLM want to do, what did the system allow, and why?

---

## Valid Scenarios

### No override

```text
original_action = RETRY
final_action = RETRY
was_overridden = False
override_reason = None
```

### Guardrail override

```text
original_action = RETRY
final_action = ESCALATE
was_overridden = True
override_reason = "Maximum retry limit reached"
```

---

## Validation

If:

```text
original_action == final_action
```

then:

```text
was_overridden = False
override_reason = None
```

If:

```text
original_action != final_action
```

then:

```text
was_overridden = True
override_reason is required
```

This prevents contradictory audit data.

The guardrail result can later be used to calculate metrics such as:

```text
Guardrail Override Rate
=
Overridden Decisions
/
Total Decisions
```

---

# Execution Contract

## `ExecutionResult`

**Location:**

```text
app/models/execution/execution_result.py
```

Represents what actually happened after the approved action was sent to the executor.

### Fields

```text
action
executed
status
message
```

---

## Validation

If:

```text
executed = True
```

then:

```text
status = EXECUTED
```

If:

```text
executed = False
```

then:

```text
status = FAILED
```

The following state is invalid:

```text
executed = True
status = FAILED
```

This contract separates:

```text
Decision quality
```

from:

```text
Execution success
```

A valid decision can still fail operationally during execution.

---

# Audit Contract

## `AuditLog`

**Location:**

```text
app/models/audit/audit_log.py
```

The audit log creates a complete trace of the recovery workflow.

### Structure

```text
audit_id
timestamp

event

customer_history
retry_history
payment_method_status

proposed_decision
guardrail_result
execution_result
```

The model composes the existing validated contracts instead of duplicating their fields.

---

## Workflow Trace

The audit log records:

```text
What triggered the workflow?
        ↓
PaymentFailedEvent

What information did the agent receive?
        ↓
CustomerHistory
RetryHistory
PaymentMethodStatus

What did the LLM propose?
        ↓
RecoveryDecision

Did guardrails change the proposal?
        ↓
GuardrailResult

What actually happened?
        ↓
ExecutionResult
```

This provides an end-to-end explanation of every recovery workflow.

---

# Validation Strategy

The project uses multiple layers of validation.

## Field-level validation

Examples:

```text
IDs cannot be empty.
Counts cannot be negative.
Messages cannot be empty.
Confidence must be between 0 and 1.
```

---

## Cross-field validation

Examples:

```text
retry_count and total_failures must be logically consistent.
```

```text
can_retry and reason_if_not_retryable cannot contradict each other.
```

```text
retry_after_minutes is required only for RETRY.
```

```text
was_overridden must match the relationship between original_action and final_action.
```

```text
executed must match ExecutionStatus.
```

The goal is to reject impossible states before they enter later stages of the system.

```text
Invalid Data
      ↓
Validation Layer
      ↓
Rejected Early
      ↓
Does Not Enter Agent Workflow
```

---

# Testing

Each major contract has unit tests covering:

* valid input
* invalid input
* field validation
* cross-field validation
* logically impossible states

The audit layer additionally tests model composition.

The test structure follows the model organization.

```text
tests/
├── test_events/
├── test_context/
├── test_decisions/
├── test_guardrails/
├── test_execution/
└── test_audit/
```

A reusable valid audit workflow helper is used when testing `AuditLog`.

This prevents unnecessary duplication when constructing nested models.

The helper must itself satisfy all existing contracts.

For example, an invalid nested event will cause every audit test to fail before the audit logic is reached.

---

# Current System Status

## Completed

```text
PHASE 0 — Architecture Decisions
├── Project scope and boundary            ✅
├── Component responsibilities            ✅
├── Failure handling strategy             ✅
├── Idempotency approach                  ✅
├── Source of truth                       ✅
├── Success and evaluation metrics        ✅
└── MongoDB database decision             ✅


PROJECT STRUCTURE
├── Folder architecture                   ✅
├── Package structure                     ✅
└── Import and testing setup              ✅


PHASE 1 — SYSTEM CONTRACTS

Shared Enums
├── RecoveryAction                        ✅
├── FailureType                           ✅
├── PaymentMethodStatusType               ✅
└── ExecutionStatus                       ✅

Event
└── PaymentFailedEvent                    ✅

Agent Context
├── CustomerHistory                       ✅
├── RetryHistory                          ✅
└── PaymentMethodStatus                   ✅

Decision
└── RecoveryDecision                      ✅

Safety
└── GuardrailResult                       ✅

Execution
└── ExecutionResult                       ✅

Observability
└── AuditLog                              ✅
```

---

# Current Architecture

The validated system backbone is now:

```text
PaymentFailedEvent
        ↓
Validated Event Contract
        ↓
Agent Context
├── CustomerHistory
├── RetryHistory
└── PaymentMethodStatus
        ↓
RecoveryDecision
        ↓
GuardrailResult
        ↓
ExecutionResult
        ↓
AuditLog
```

Every major stage in the workflow now has a clearly defined and validated contract.

---

# Next Steps

The next implementation phase will build the actual behavior around these contracts.

```text
1. Context retrieval tools
        ↓
2. Agent orchestration
        ↓
3. LLM decision generation
        ↓
4. Deterministic guardrail logic
        ↓
5. Action execution
        ↓
6. MongoDB persistence
        ↓
7. Audit logging
        ↓
8. End-to-end workflow integration
        ↓
9. Evaluation and testing
```

The architecture should continue following one important rule:

```text
Raw or external data
        ↓
Validate into a structured model
        ↓
Pass validated contracts between components
        ↓
Avoid unstructured dictionaries for core workflow data
```

---

# Final Architecture Principle

This project is not designed as:

```text
Payment failed
      ↓
Ask LLM what to do
      ↓
Execute response
```

It is designed as:

```text
Payment failed
      ↓
Validate event
      ↓
Collect structured context
      ↓
LLM proposes a bounded action
      ↓
Validate decision
      ↓
Apply deterministic guardrails
      ↓
Execute approved action
      ↓
Record the complete workflow
      ↓
Evaluate system performance
```

The objective is to build a payment recovery agent that is not only capable of making decisions, but is also:

* structured
* bounded
* testable
* auditable
* explainable
* safe to evaluate
* extensible for future recovery scenarios
