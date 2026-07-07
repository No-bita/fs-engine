from pydantic import BaseModel, ConfigDict, Field
from models.taxonomy import WorkflowActor, WorkflowChannel

class WorkflowStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., pattern=r"^[A-Z0-9_]+$", description="Canonical ID for workflow step, e.g., PMEGP_WF_STEP_01")
    step_number: int = Field(..., gt=0, description="Sequence order of the step")
    name: str = Field(..., description="Name of the step")
    description: str = Field(..., description="Actionable detail of the step")
    actor: WorkflowActor = Field(..., description="Who performs the step")
    channel: WorkflowChannel = Field(..., description="How the step is executed")
    url: str = Field("", description="Optional URL related to this step")
    estimated_duration_days: int = Field(0, ge=0, description="Estimated duration in days, 0 if immediate/unknown")
