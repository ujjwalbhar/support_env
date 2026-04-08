from typing import Optional, Literal
from pydantic import Field
from openenv.core.env_server.types import Action, Observation, State


class SupportAction(Action):
    """Action taken by the AI agent on a customer support ticket."""

    action_type: Literal["classify", "respond", "escalate", "resolve"] = Field(
        ...,
        description=(
            "Type of action: "
            "'classify' - categorize the email, "
            "'respond' - generate a reply, "
            "'escalate' - escalate to human agent, "
            "'resolve' - mark as resolved"
        ),
    )
    category: Optional[Literal["complaint", "refund", "inquiry", "technical", "billing"]] = Field(
        None,
        description="Email category (required when action_type is 'classify')",
    )
    response_text: Optional[str] = Field(
        None,
        description="Response message to the customer (required when action_type is 'respond')",
    )
    escalation_reason: Optional[str] = Field(
        None,
        description="Reason for escalation (required when action_type is 'escalate')",
    )
    resolution_summary: Optional[str] = Field(
        None,
        description="Summary of resolution (required when action_type is 'resolve')",
    )


class SupportObservation(Observation):
    """Observation returned to the agent after each action."""

    email_id: str = Field(..., description="Unique identifier for the current email ticket")
    email_subject: str = Field(..., description="Subject line of the customer email")
    email_body: str = Field(..., description="Body content of the customer email")
    customer_name: str = Field(..., description="Name of the customer")
    customer_tier: Literal["standard", "premium", "enterprise"] = Field(
        ..., description="Customer subscription tier"
    )
    previous_interactions: int = Field(
        ..., description="Number of previous support interactions by this customer"
    )
    current_category: Optional[str] = Field(
        None, description="Current classification of the ticket (None if not yet classified)"
    )
    action_feedback: str = Field(
        ..., description="Feedback on the last action taken"
    )
    task_complete: bool = Field(
        False, description="Whether the current task has been completed"
    )
    reward: float = Field(
        0.0, description="Reward signal for the last action (0.0 - 1.0)"
    )
    task_id: str = Field(..., description="Current task identifier (easy/medium/hard)")


class SupportState(State):
    """Tracks episode-level metadata."""

    current_task: str = Field("easy", description="Current difficulty task")
    emails_processed: int = Field(0, description="Number of emails processed this episode")
    total_reward: float = Field(0.0, description="Cumulative reward this episode")
    classification_correct: Optional[bool] = Field(
        None, description="Whether the last classification was correct"
    )
