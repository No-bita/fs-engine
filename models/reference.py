from pydantic import BaseModel, ConfigDict, Field
from models.taxonomy import ReferenceType

class Reference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., pattern=r"^[A-Z0-9_]+$", description="Canonical ID for reference, e.g., PMEGP_REF_01")
    title: str = Field(..., description="Title of the reference")
    url: str = Field(..., pattern=r"^https?://.+$", description="URL of the reference source")
    type: ReferenceType = Field(..., description="Strong category type of reference source")
    language: str = Field("en", description="Language of the reference source")
