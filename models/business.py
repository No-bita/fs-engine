from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

class BusinessProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Stage 1: Identity & Location
    name: Optional[str] = Field(None, description="Business name")
    state: Optional[str] = Field(None, description="State of operation")
    district: Optional[str] = Field(None, description="District of operation")
    constitution: Optional[str] = Field(None, description="proprietorship, partnership, private_limited, etc.")

    # Stage 2: Financials & Operations
    sector: Optional[str] = Field(None, description="manufacturing, services, trading, agriculture_allied")
    msme_segment: Optional[str] = Field(None, description="micro, small, medium")
    turnover: Optional[float] = Field(None, description="Annual Turnover in INR")
    investment_plant_machinery: Optional[float] = Field(None, description="Investment in plant and machinery in INR")
    establishment_year: Optional[int] = Field(None, description="Year of establishment")

    # Stage 3: Registrations & Demographics
    ownership_category: Optional[str] = Field(None, description="SC, ST, women, general, OBC")
    has_udyam_registration: Optional[bool] = Field(None, description="Whether business has Udyam registration")
    export_status: Optional[str] = Field(None, description="exporter, non_exporter")
    employment_count: Optional[int] = Field(None, description="Number of employees")
