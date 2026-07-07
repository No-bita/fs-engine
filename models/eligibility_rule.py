from pydantic import BaseModel, ConfigDict, Field
from typing import Any
from models.taxonomy import RuleParameter, RuleOperator

class EligibilityRule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., pattern=r"^[A-Z0-9_]+$", description="Canonical ID for rule, e.g., PMEGP_RULE_TURNOVER")
    parameter: RuleParameter = Field(..., description="The business profile parameter to evaluate")
    operator: RuleOperator = Field(..., description="Comparison operator")
    value: Any = Field(..., description="The matching value or threshold")
