from enum import Enum

class SchemeType(str, Enum):
    GOVERNMENT_SCHEME = "government_scheme"
    GOVERNMENT_PRODUCT = "government_product"
    CREDIT_GUARANTEE = "credit_guarantee"
    PROCUREMENT_PROGRAM = "procurement_program"
    TAX_INCENTIVE = "tax_incentive"
    SUBSIDY = "subsidy"
    GRANT = "grant"

class GovernmentLevel(str, Enum):
    CENTRAL = "central"
    STATE = "state"
    DISTRICT = "district"
    PSU = "psu"
    BANK = "bank"
    MULTILATERAL = "multilateral"

class ActiveStatus(str, Enum):
    CONFIRMED_ACTIVE = "confirmed_active"
    TEMPORARILY_CLOSED = "temporarily_closed"
    EXPIRED = "expired"
    MERGED = "merged"
    DRAFT = "draft"
    UNKNOWN = "unknown"

class PriorityTier(str, Enum):
    TIER_1 = "tier_1"
    TIER_2 = "tier_2"
    TIER_3 = "tier_3"

class ProviderCategory(str, Enum):
    CENTRAL_GOVERNMENT = "central_government"
    STATE_GOVERNMENT = "state_government"
    FINANCIAL_INSTITUTION = "financial_institution"
    PUBLIC_INSTITUTION = "public_institution"
    PRIVATE_SECTOR = "private_sector"
    UNKNOWN = "unknown"

class GeographyCoverage(str, Enum):
    ALL_INDIA = "all_india"
    STATE_SPECIFIC = "state_specific"
    DISTRICT_SPECIFIC = "district_specific"

class BenefitCategory(str, Enum):
    SUBSIDY = "subsidy"
    LOAN = "loan"
    GUARANTEE = "guarantee"
    GRANT = "grant"
    INTEREST_SUBVENTION = "interest_subvention"
    TAX_INCENTIVE = "tax_incentive"
    PROCUREMENT = "procurement"
    INSURANCE_RISK_COVER = "insurance_risk_cover"
    REIMBURSEMENT = "reimbursement"
    OTHER = "other"

class WorkflowActor(str, Enum):
    APPLICANT = "applicant"
    PROVIDER = "provider"
    IMPLEMENTING_AGENCY = "implementing_agency"
    BANK = "bank"
    THIRD_PARTY = "third_party"

class WorkflowChannel(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    HYBRID = "hybrid"

class ReferenceType(str, Enum):
    OFFICIAL_GUIDELINES = "official_guidelines"
    APPLICATION_PORTAL = "application_portal"
    FAQ = "faq"
    CIRCULAR = "circular"
    PRESS_RELEASE = "press_release"
    THIRD_PARTY = "third_party"

class RuleOperator(str, Enum):
    EQUAL = "="
    NOT_EQUAL = "!="
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    IN = "IN"
    NOT_IN = "NOT IN"
    BETWEEN = "BETWEEN"
    CONTAINS = "CONTAINS"

class RuleParameter(str, Enum):
    BUSINESS_MSME_SEGMENT = "business.msme_segment"
    BUSINESS_TURNOVER = "business.turnover"
    BUSINESS_STATE = "business.state"
    BUSINESS_DISTRICT = "business.district"
    BUSINESS_SECTOR = "business.sector"
    BUSINESS_OWNERSHIP_CATEGORY = "business.ownership_category"
    BUSINESS_CONSTITUTION = "business.constitution"
    BUSINESS_INVESTMENT_PLANT_MACHINERY = "business.investment_plant_machinery"
    BUSINESS_ESTABLISHMENT_YEAR = "business.establishment_year"
    BUSINESS_HAS_UDYAM_REGISTRATION = "business.has_udyam_registration"
    BUSINESS_EMPLOYMENT_COUNT = "business.employment_count"
    BUSINESS_EXPORT_STATUS = "business.export_status"

class SourceConfidence(str, Enum):
    OFFICIAL = "official"
    SEMI_OFFICIAL = "semi_official"
    THIRD_PARTY = "third_party"
    CROWDSOURCED = "crowdsourced"
