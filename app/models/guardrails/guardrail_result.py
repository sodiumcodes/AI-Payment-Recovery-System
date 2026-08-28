from pydantic import BaseModel, model_validator
from app.models.enums import RecoveryAction

class GuardrailResult(BaseModel):
    """
    Represents the result of deterministic guardrail evaluation.

    It records the action originally proposed by the LLM, the final action approved by the system, and whether the original decision was overridden.
    """

    # The action originally proposed by the LLM.
    original_action: RecoveryAction

    # The final action approved after guardrail evaluation.
    final_action: RecoveryAction

    # Indicates whether the guardrail changed the LLM's proposed action.
    was_overridden: bool

    # Explains why the original action was overridden.
    # This is only relevant when was_overridden is True.
    override_reason: str | None = None

    @model_validator(mode="after")
    def validate_guardrail_result(self):
       #Validates that the original action, final action, override flag, and override reason are logically consistent.

        # If the original and final actions are the same, the decision was not overridden. Therefore, was_overridden must be False and there should be no override reason.
        if self.original_action == self.final_action:
            if self.was_overridden:
                raise ValueError(
                    "was_overridden must be False when actions are the same"
                )

            if self.override_reason is not None:
                raise ValueError(
                    "override_reason must be None when no override occurred"
                )

        # If the final action differs from the original action, the guardrail must have overridden the LLM's proposed decision.
        else:
            if not self.was_overridden:
                raise ValueError(
                    "was_overridden must be True when actions are different"
                )

            # An override without an explanation would make the system difficult to audit and debug.
            if not self.override_reason:
                raise ValueError(
                    "override_reason is required when an override occurs"
                )

        return self