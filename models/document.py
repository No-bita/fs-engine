from pydantic import BaseModel, ConfigDict, Field

class DocumentRequirement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., pattern=r"^[A-Z0-9_]+$", description="Canonical ID for document, e.g., DOC_UDYAM_REGISTRATION")
    name: str = Field(..., description="Name of the document")
    description: str = Field("", description="Purpose or description of the document")
    is_mandatory: bool = Field(True, description="Whether the document is mandatory")
    issuing_authority: str = Field("", description="Authority issuing the document")
    digitized_verification_available: bool = Field(False, description="Whether digitized API verification is available")
