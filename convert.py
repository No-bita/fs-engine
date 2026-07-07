import os
import pandas as pd
import json
import re
from pathlib import Path
from models import (
    SchemeDocument, SchemeIdentity, Provider, Geography, Tags, Metadata,
    Benefit, EligibilityRule, DocumentRequirement, WorkflowStep, Reference
)

def clean_tag_list(val):
    if pd.isna(val) or val == 'unknown' or val == 'not_applicable':
        return []
    return [t.strip() for t in str(val).split('|') if t.strip()]

def clean_id(s: str) -> str:
    s = s.upper().strip()
    s = re.sub(r'[^\w\s]', '', s)
    s = re.sub(r'[\s-]+', '_', s)
    return s

def slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s_]+', '-', s)
    return s.strip('-')

def extract_acronym(name: str) -> str:
    acronyms = re.findall(r'\b[A-Z]{2,10}\b', name)
    if acronyms:
        return acronyms[0]
    parts = [w for w in name.split() if w[0].isupper()]
    if len(parts) >= 2:
        return "".join(w[0] for w in parts)[:10]
    return name[:10].upper()

def map_scheme_type(old_type: str, financial_instrument: str) -> str:
    ot = str(old_type).lower()
    fi = str(financial_instrument).lower() if pd.notna(financial_instrument) else ""
    
    if "grant" in fi or "grant" in ot:
        return "grant"
    elif "subsidy" in fi or "subsidy" in ot:
        return "subsidy"
    elif "guarantee" in fi or "guarantee" in ot:
        return "credit_guarantee"
    elif "procurement" in ot or "procurement" in fi:
        return "procurement_program"
    elif "tax" in fi or "duty" in fi or "tax" in ot:
        return "tax_incentive"
    elif "loan" in fi or "credit" in fi or "finance" in ot:
        return "government_product"
    else:
        return "government_scheme"

def map_provider_category(pc: str) -> str:
    pc = str(pc).lower()
    if "central_government" in pc:
        return "central_government"
    elif "state_government" in pc:
        return "state_government"
    elif "finance" in pc or "bank" in pc:
        return "financial_institution"
    elif "public" in pc or "psu" in pc:
        return "public_institution"
    return "unknown"

def map_benefit_category(tags) -> str:
    if not tags:
        return "other"
    for t in tags:
        t_low = t.lower()
        if "subsidy" in t_low:
            return "subsidy"
        elif "loan" in t_low or "credit" in t_low:
            return "loan"
        elif "guarantee" in t_low:
            return "guarantee"
        elif "grant" in t_low:
            return "grant"
        elif "subvention" in t_low:
            return "interest_subvention"
        elif "tax" in t_low or "duty" in t_low:
            return "tax_incentive"
        elif "procurement" in t_low:
            return "procurement"
        elif "insurance" in t_low or "risk" in t_low:
            return "insurance_risk_cover"
        elif "reimbursement" in t_low:
            return "reimbursement"
    return "other"

def parse_float(val) -> float:
    if pd.isna(val) or not val:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    val_str = str(val).lower()
    if val_str in ("unknown", "not_applicable", "none", ""):
        return 0.0
    match = re.search(r'[\d\.]+', val_str)
    if match:
        try:
            return float(match.group(0))
        except ValueError:
            return 0.0
    return 0.0

def parse_months(s: str) -> int:
    if pd.isna(s) or not s or not isinstance(s, str):
        return 0
    s = s.lower()
    if s in ("unknown", "not_applicable", "none"):
        return 0
    if "year" in s:
        match = re.search(r'(\d+)\s*year', s)
        if match:
            return int(match.group(1)) * 12
    match = re.search(r'(\d+)\s*month', s)
    if match:
        return int(match.group(1))
    match = re.search(r'\d+', s)
    if match:
        return int(match.group(0))
    return 0

def format_date(d: str) -> str:
    if pd.isna(d) or not d or str(d).lower() in ("unknown", "none"):
        return ""
    d_str = str(d).strip()
    if re.match(r'^\d{4}-\d{2}-\d{2}$', d_str):
        return f"{d_str}T00:00:00Z"
    return d_str

def main():
    csv_path = "/Users/aaryanshah/Downloads/FS Engine/MSME Benefits Central C1 C5.csv"
    if not os.path.exists(csv_path):
        print(f"CSV file not found at {csv_path}")
        return

    df = pd.read_csv(csv_path)

    # Group rows by scheme_or_product_name to combine benefits
    grouped = df.groupby("scheme_or_product_name")

    for scheme_name, group in grouped:
        first_row = group.iloc[0]
        sch_id = clean_id(scheme_name)
        slug = slugify(scheme_name)
        short_name = extract_acronym(scheme_name)
        
        # Build benefits list
        benefits = []
        benefit_cat_tags = []
        for idx, (_, row) in enumerate(group.iterrows()):
            ben_id = f"{sch_id}_BENEFIT_{idx+1:02d}"
            cats = clean_tag_list(row.get("benefit_category_tags", ""))
            benefit_cat_tags.extend(cats)
            
            cat = map_benefit_category(cats)
            
            coll_req_str = str(row.get("collateral_requirement", "unknown"))
            collateral_required = not ("collateral_free" in coll_req_str or "no_collateral" in coll_req_str or coll_req_str == "not_applicable")

            benefits.append(Benefit(
                id=ben_id,
                name=row["benefit_name"],
                category=cat,
                summary=str(row.get("benefit_summary", "")),
                calculation_logic=None if pd.isna(row.get("benefit_calculation_logic")) else str(row.get("benefit_calculation_logic")),
                max_amount=parse_float(row.get("maximum_benefit_amount")),
                min_amount=parse_float(row.get("minimum_benefit_amount")),
                loan_range="" if pd.isna(row.get("loan_amount_range")) else str(row.get("loan_amount_range")),
                interest_rate="" if pd.isna(row.get("interest_rate_or_subvention")) else str(row.get("interest_rate_or_subvention")),
                collateral_required=collateral_required,
                collateral_details=coll_req_str if coll_req_str != "not_applicable" else "",
                guarantee_coverage="" if pd.isna(row.get("guarantee_coverage")) else str(row.get("guarantee_coverage")),
                tenure_months=parse_months(row.get("repayment_tenure")),
                moratorium_months=parse_months(row.get("moratorium")),
                margin_contribution="" if pd.isna(row.get("margin_contribution_required")) else str(row.get("margin_contribution_required"))
            ))

        # Build bootstrap eligibility rules
        eligibility_rules = []
        msme_segment_tags = clean_tag_list(first_row.get("msme_segment_tags", ""))
        if "micro" in [m.lower() for m in msme_segment_tags]:
            eligibility_rules.append(EligibilityRule(
                id=f"{sch_id}_RULE_01",
                parameter="business.msme_segment",
                operator="IN",
                value=["micro", "small"]
            ))

        # References
        refs = []
        ref_idx = 1
        for col in ["official_source_url", "policy_document_url", "secondary_source_url"]:
            url_val = first_row.get(col)
            if pd.notna(url_val) and url_val != "unknown" and str(url_val).startswith("http"):
                ref_type = "third_party"
                title = col.replace("_", " ").title()
                if "official" in title.lower() or "policy" in title.lower():
                    ref_type = "official_guidelines"
                elif "portal" in title.lower() or "apply" in title.lower():
                    ref_type = "application_portal"

                refs.append(Reference(
                    id=f"{sch_id}_REF_{ref_idx:02d}",
                    title=title,
                    url=str(url_val),
                    type=ref_type,
                    language="en"
                ))
                ref_idx += 1

        # Geography
        state_or_ut = str(first_row.get("state_or_ut", "all_india"))
        geo_coverage = "all_india" if state_or_ut == "all_india" else "state_specific"
        geo_states = [] if state_or_ut == "all_india" else [state_or_ut]

        # Priority
        old_priority = str(first_row.get("priority_tier", "tier_2_segment_specific"))
        if "tier_1" in old_priority:
            priority = "tier_1"
        elif "tier_3" in old_priority:
            priority = "tier_3"
        else:
            priority = "tier_2"

        # Provider category & government level
        category = map_provider_category(first_row.get("provider_category", "unknown"))
        gov_level = "central" if "central" in str(first_row.get("government_level", "central")).lower() else "state"

        provider = Provider(
            category=category,
            name=str(first_row["provider_name"]),
            implementing_agencies=[],
            government_level=gov_level
        )

        geography = Geography(
            coverage=geo_coverage,
            states=geo_states,
            districts=[]
        )

        tags = Tags(
            business_stages=clean_tag_list(first_row.get("business_stage_tags", "")),
            sectors=clean_tag_list(first_row.get("sector_tags", "")),
            benefit_categories=list(set(benefit_cat_tags)),
            msme_segments=msme_segment_tags,
            business_intents=[]
        )

        scheme_type = map_scheme_type(first_row["scheme_type"], first_row.get("financial_instrument_type", ""))
        scheme_identity = SchemeIdentity(
            id=sch_id,
            name=scheme_name,
            short_name=short_name,
            slug=slug,
            description="",
            scheme_type=scheme_type,
            provider=provider,
            geography=geography,
            tags=tags,
            status="confirmed_active" if str(first_row["active_status"]) == "confirmed_active" else "unknown",
            priority=priority
        )

        last_verified = format_date(first_row.get("last_verified_date", ""))
        metadata = Metadata(
            created_at=last_verified,
            updated_at=last_verified,
            verified_at=last_verified,
            source_confidence="official",
            compiled_by="migration_bot",
            reviewed_by="admin",
            quality_score=100,
            notes=None if pd.isna(first_row.get("notes")) else str(first_row.get("notes"))
        )

        scheme_doc = SchemeDocument(
            schema_version="1.0.0",
            scheme=scheme_identity,
            benefits=benefits,
            eligibility_rules=eligibility_rules,
            documents=[],
            workflow=[],
            references=refs,
            metadata=metadata
        )

        # Sanitize filename
        safe_filename = "".join([c if c.isalnum() or c in (' ', '_', '-') else '' for c in scheme_name]).replace(' ', '_')
        output_file = Path("/Users/aaryanshah/Downloads/FS Engine/data/json") / f"{safe_filename}.json"
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(scheme_doc.model_dump(), f, indent=4, ensure_ascii=False)

    print("Successfully converted CSV rows to Canonical JSON files conforming to the new Pydantic schema.")

if __name__ == "__main__":
    main()
