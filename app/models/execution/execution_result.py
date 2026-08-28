from pydantic import BaseModel, Field, model_validator
from app.models.enums import ExecutionStatus, RecoveryAction

class ExecutionResult(BaseModel):
    """
    Represents the outcome of executing an approved recovery action.

    This model records what action the executor attempted and whether
    the execution was successful or failed.
    """

    # The recovery action that the executor attempted to perform.
    action: RecoveryAction

    # Indicates whether the action was successfully executed.
    executed: bool

    # Represents the final execution outcome using a controlled
    # set of allowed values.
    status: ExecutionStatus

    # Provides a human-readable explanation of the execution result.
    # This is useful for debugging and auditing.
    message: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_execution_result(self):
        """
        Validates that the execution flag and execution status
        describe the same outcome.
        """

        # A successfully executed action must have the EXECUTED status.
        if (
            self.executed
            and self.status != ExecutionStatus.EXECUTED
        ):
            raise ValueError(
                "status must be EXECUTED when executed is True"
            )

        # A failed execution must have the FAILED status.
        if (
            not self.executed
            and self.status != ExecutionStatus.FAILED
        ):
            raise ValueError(
                "status must be FAILED when executed is False"
            )

        return self