from pydantic import BaseModel, ConfigDict, Field
from models.taxonomy import BenefitCategory

class Benefit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., pattern=r"^[A-Z0-9_]+$", description="Canonical ID for benefit, e.g., PMEGP_BENEFIT_SUBSIDY")
    name: str = Field(..., description="Name of the benefit")
    category: BenefitCategory = Field(..., description="Category of benefit")
    summary: str = Field(..., description="Summary of the benefit details")
    calculation_logic: str = Field("", description="Calculation logic details")
    max_amount: float = Field(0.0, ge=0.0, description="Max benefit amount in INR, 0.0 if not capped/unknown")
    min_amount: float = Field(0.0, ge=0.0, description="Min benefit amount in INR")
    loan_range: str = Field("", description="Applicable loan range string if any")
    interest_rate: str = Field("", description="Interest rate or subvention info")
    collateral_required: bool = Field(False, description="Whether collateral is required")
    collateral_details: str = Field("", description="Collateral details if any")
    guarantee_coverage: str = Field("", description="Guarantee coverage percentage or details")
    tenure_months: int = Field(0, ge=0, description="Repayment tenure in months, 0 if unknown/NA")
    moratorium_months: int = Field(0, ge=0, description="Moratorium period in months")
    margin_contribution: str = Field("", description="Margin contribution required")
