from pydantic import BaseModel, ConfigDict, Field
from typing import List
from models.taxonomy import (
    SchemeType, ProviderCategory, GovernmentLevel, GeographyCoverage,
    ActiveStatus, PriorityTier, SourceConfidence
)
from models.benefit import Benefit
from models.eligibility_rule import EligibilityRule
from models.document import DocumentRequirement
from models.workflow import WorkflowStep
from models.reference import Reference

class Provider(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: ProviderCategory = Field(..., description="Provider category")
    name: str = Field(..., description="Full name of the providing ministry or organization")
    implementing_agencies: List[str] = Field(default_factory=list, description="Agencies implementing the scheme")
    government_level: GovernmentLevel = Field(..., description="Level of government providing the scheme")

class Geography(BaseModel):
    model_config = ConfigDict(extra="forbid")

    coverage: GeographyCoverage = Field(..., description="Geography coverage level")
    states: List[str] = Field(default_factory=list, description="States where the scheme is applicable")
    districts: List[str] = Field(default_factory=list, description="Districts where the scheme is applicable")

class Tags(BaseModel):
    model_config = ConfigDict(extra="forbid")

    business_stages: List[str] = Field(default_factory=list, description="Target stages of business")
    sectors: List[str] = Field(default_factory=list, description="Target industry sectors")
    benefit_categories: List[str] = Field(default_factory=list, description="Tags describing categories of benefits")
    msme_segments: List[str] = Field(default_factory=list, description="Target MSME segments")
    business_intents: List[str] = Field(default_factory=list, description="Target business intents")
    search_keywords: List[str] = Field(default_factory=list, description="Search keywords and synonyms")
    search_aliases: List[str] = Field(default_factory=list, description="Common abbreviations or alternative names")

class FaqItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str = Field(..., description="The FAQ question")
    answer: str = Field(..., description="The FAQ answer")

class SchemeIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., pattern=r"^[A-Z0-9_]+$", description="Canonical unique ID, e.g., PMEGP")
    name: str = Field(..., description="Full name of the scheme")
    short_name: str = Field(..., description="Short/abbreviated name of the scheme")
    slug: str = Field(..., pattern=r"^[a-z0-9-]+$", description="Lowercase kebab-case slug")
    description: str = Field("", description="Detailed description of the scheme identity")
    scheme_type: SchemeType = Field(..., description="Type of the scheme")
    provider: Provider = Field(..., description="Provider organization information")
    geography: Geography = Field(..., description="Geographic applicability")
    tags: Tags = Field(..., description="Search and categorization tags")
    status: ActiveStatus = Field(..., description="Active status of the scheme")
    priority: PriorityTier = Field(..., description="Registry display/processing priority tier")

class Metadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    created_at: str = Field("", pattern=r"^$|^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?)?$", description="ISO-8601 creation timestamp")
    updated_at: str = Field("", pattern=r"^$|^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?)?$", description="ISO-8601 update timestamp")
    verified_at: str = Field("", pattern=r"^$|^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?)?$", description="ISO-8601 verification timestamp")
    source_confidence: SourceConfidence = Field(..., description="Confidence score or level of source verification")
    compiled_by: str = Field("", description="Name of the person/bot who compiled the scheme data")
    reviewed_by: str = Field("", description="Name of the person who reviewed the scheme data")
    quality_score: int = Field(100, ge=0, le=100, description="Calculated completeness and quality score (0-100)")
    notes: str = Field("", description="Internal developer or compiler notes")

class SchemeDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = Field("1.0.0", description="Version of this document schema")
    scheme: SchemeIdentity = Field(..., description="Scheme core identity details")
    benefits: List[Benefit] = Field(default_factory=list, description="List of benefits provided by the scheme")
    eligibility_rules: List[EligibilityRule] = Field(default_factory=list, description="Rules to determine business eligibility")
    documents: List[DocumentRequirement] = Field(default_factory=list, description="Documents required to apply")
    workflow: List[WorkflowStep] = Field(default_factory=list, description="Step-by-step application workflow")
    references: List[Reference] = Field(default_factory=list, description="Reference links and documents")
    metadata: Metadata = Field(..., description="Curation metadata")
    suggested_faqs: List[FaqItem] = Field(default_factory=list, description="List of suggested FAQs for this scheme")
