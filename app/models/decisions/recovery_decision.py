from pydantic import BaseModel, Field, model_validator
from app.models.enums import RecoveryAction

class RecoveryDecision(BaseModel):
    """
    Represents the recovery action proposed by the LLM.
    This is only a proposed decision. The decision must still pass
    through deterministic guardrails before it can be executed.
    """

    # The recovery action proposed by the agent. Using an enum restricts the agent to a fixed decision space.
    action: RecoveryAction

    # Specifies how long the system should wait before retrying. This is only relevant when the proposed action is RETRY.
    retry_after_minutes: int | None = None

    # Explains why the agent selected the proposed action. A decision without a reason is not useful for auditing or debugging.
    reason: str = Field(min_length=1)

    # Represents the model's confidence in its proposed decision.
    # Confidence is bounded between 0 and 1, but it does not guarantee that the decision is correct.
    confidence: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_retry_decision(self):
        #Validates relationships between the proposed action and retry-specific information.
        
        # If the agent proposes a retry, it must specify when the retry should happen. The delay must also be greater than zero.
        if self.action == RecoveryAction.RETRY:
            if self.retry_after_minutes is None:
                raise ValueError(
                    "retry_after_minutes is required when action is retry"
                )

            if self.retry_after_minutes <= 0:
                raise ValueError(
                    "retry_after_minutes must be greater than 0"
                )

        # If the agent proposes any action other than retry, retry timing should not be included because it would be contradictory data.
        elif self.retry_after_minutes is not None:
            raise ValueError(
                "retry_after_minutes must be None when action is not retry"
            )
        
        return self