import json
import re
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from models import (
    SchemeDocument, SchemeIdentity, Provider, Geography, Tags, Metadata,
    Benefit, EligibilityRule, DocumentRequirement, WorkflowStep, Reference
)

def slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s_]+', '-', s)
    return s.strip('-')

def clean_id(s: str) -> str:
    s = s.upper().strip()
    s = re.sub(r'[^\w\s]', '', s)
    s = re.sub(r'[\s-]+', '_', s)
    return s

def extract_acronym(name: str, filename_stem: str) -> str:
    # Look for all uppercase acronyms of length 2-10 in the name
    acronyms = re.findall(r'\b[A-Z]{2,10}\b', name)
    if acronyms:
        return acronyms[0]
    # Check filename stem for uppercase acronym
    acronyms_fn = re.findall(r'\b[A-Z]{2,10}\b', filename_stem.replace('_', ' '))
    if acronyms_fn:
        return acronyms_fn[0]
    # Fallback: take first letters of each title-case word
    parts = [w for w in name.split() if w[0].isupper()]
    if len(parts) >= 2:
        return "".join(w[0] for w in parts)[:10]
    return name[:10].upper()

def map_scheme_type(old_type: str, financial_instrument: str) -> str:
    ot = old_type.lower()
    fi = financial_instrument.lower() if financial_instrument else ""
    
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
    pc = pc.lower()
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
    if not val:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    val_str = str(val).lower()
    if val_str in ("unknown", "not_applicable", "none", ""):
        return 0.0
    # Try to extract numbers
    match = re.search(r'[\d\.]+', val_str)
    if match:
        try:
            return float(match.group(0))
        except ValueError:
            return 0.0
    return 0.0

def parse_months(s: str) -> int:
    if not s or not isinstance(s, str):
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
    if not d or d.lower() in ("unknown", "none"):
        return ""
    # Check if matches ISO format already
    if re.match(r'^\d{4}-\d{2}-\d{2}$', d):
        return f"{d}T00:00:00Z"
    return d

def main():
    json_dir = project_root / "data" / "json"
    if not json_dir.exists():
        print(f"Data directory {json_dir} does not exist!")
        return

    json_files = list(json_dir.glob("*.json"))
    print(f"Found {len(json_files)} JSON files to migrate.")

    success_count = 0
    for file_path in json_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                old_data = json.load(f)

            # Skip if already migrated (has schema_version "1.0.0" and is already new schema)
            if "schema_version" in old_data and old_data["schema_version"] == "1.0.0" and "scheme" in old_data and isinstance(old_data["scheme"], dict) and "id" in old_data["scheme"]:
                print(f"Skipping already migrated file: {file_path.name}")
                success_count += 1
                continue

            filename_stem = file_path.stem
            name = old_data.get("scheme_or_product_name", filename_stem.replace("_", " "))
            
            # Extract standard parts
            sch_id = clean_id(filename_stem)
            slug = slugify(name)
            short_name = extract_acronym(name, filename_stem)
            
            # Geography
            state_or_ut = old_data.get("state_or_ut", "all_india")
            geo_coverage = "all_india" if state_or_ut == "all_india" else "state_specific"
            geo_states = [] if state_or_ut == "all_india" else [state_or_ut]

            # Priority
            old_priority = old_data.get("priority_tier", "tier_2_segment_specific")
            if "tier_1" in old_priority:
                priority = "tier_1"
            elif "tier_3" in old_priority:
                priority = "tier_3"
            else:
                priority = "tier_2"

            # Provider Category
            category = map_provider_category(old_data.get("provider_category", "unknown"))
            # Provider level
            gov_level = "central" if "central" in old_data.get("government_level", "central").lower() else "state"

            # Tags
            business_stages = old_data.get("business_stage_tags", [])
            sectors = old_data.get("sector_tags", [])
            msme_segments = old_data.get("msme_segment_tags", [])

            # Extract benefit categories tags from old benefits
            benefit_cat_tags = []
            for b in old_data.get("benefits", []):
                benefit_cat_tags.extend(b.get("benefit_category_tags", []))
            benefit_cat_tags = list(set(benefit_cat_tags))

            # Build Provider
            provider = Provider(
                category=category,
                name=old_data.get("provider_name", "Unknown Provider"),
                implementing_agencies=[],
                government_level=gov_level
            )

            # Build Geography
            geography = Geography(
                coverage=geo_coverage,
                states=geo_states,
                districts=[]
            )

            # Build Tags
            tags = Tags(
                business_stages=business_stages,
                sectors=sectors,
                benefit_categories=benefit_cat_tags,
                msme_segments=msme_segments,
                business_intents=[]
            )

            # Build SchemeIdentity
            scheme_type = map_scheme_type(old_data.get("scheme_type", "government_scheme"), old_data.get("financial_instrument_type", ""))
            scheme_identity = SchemeIdentity(
                id=sch_id,
                name=name,
                short_name=short_name,
                slug=slug,
                description="",
                scheme_type=scheme_type,
                provider=provider,
                geography=geography,
                tags=tags,
                status="confirmed_active" if old_data.get("active_status") == "confirmed_active" else "unknown",
                priority=priority
            )

            # Build Benefits
            benefits = []
            for i, b in enumerate(old_data.get("benefits", [])):
                ben_id = f"{sch_id}_BENEFIT_{i+1:02d}"
                cat = map_benefit_category(b.get("benefit_category_tags", []))
                
                # Collateral details
                coll_req_str = b.get("collateral_requirement", "unknown")
                collateral_required = not ("collateral_free" in coll_req_str or "no_collateral" in coll_req_str or coll_req_str == "not_applicable")

                benefits.append(Benefit(
                    id=ben_id,
                    name=b.get("benefit_name", "Benefit"),
                    category=cat,
                    summary=b.get("benefit_summary", ""),
                    calculation_logic=b.get("benefit_calculation_logic") or "",
                    max_amount=parse_float(b.get("maximum_benefit_amount")),
                    min_amount=parse_float(b.get("minimum_benefit_amount")),
                    loan_range=b.get("loan_amount_range") or "",
                    interest_rate=b.get("interest_rate_or_subvention") or "",
                    collateral_required=collateral_required,
                    collateral_details=coll_req_str if coll_req_str != "not_applicable" else "",
                    guarantee_coverage=b.get("guarantee_coverage") or "",
                    tenure_months=parse_months(b.get("repayment_tenure")),
                    moratorium_months=parse_months(b.get("moratorium")),
                    margin_contribution=b.get("margin_contribution_required") or ""
                ))

            # Build Eligibility Rules
            eligibility_rules = []
            for i, r in enumerate(old_data.get("eligibility_rules", [])):
                rule_id = f"{sch_id}_RULE_{i+1:02d}"
                param = r.get("parameter", "business.msme_segment")
                # Clean parameter path in case it is slightly different
                if not param.startswith("business."):
                    param = f"business.{param}"

                eligibility_rules.append(EligibilityRule(
                    id=rule_id,
                    parameter=param,
                    operator=r.get("operator", "="),
                    value=r.get("value")
                ))

            # Build Documents
            documents = []
            for i, d in enumerate(old_data.get("documents", [])):
                doc_id = f"{sch_id}_DOC_{i+1:02d}"
                documents.append(DocumentRequirement(
                    id=doc_id,
                    name=d.get("document_name", "Required Document"),
                    description=d.get("purpose", ""),
                    is_mandatory=d.get("is_mandatory", True),
                    issuing_authority="",
                    digitized_verification_available=False
                ))

            # Build Workflow
            workflow = []
            for i, w in enumerate(old_data.get("workflow", [])):
                wf_id = f"{sch_id}_WF_{i+1:02d}"
                workflow.append(WorkflowStep(
                    id=wf_id,
                    step_number=w.get("step_number", i+1),
                    name=w.get("action", "Step"),
                    description=w.get("action", ""),
                    actor="applicant" if "applicant" in w.get("responsible_party", "").lower() else "implementing_agency",
                    channel="online",
                    url=w.get("url_or_channel", "") if w.get("url_or_channel", "").startswith("http") else "",
                    estimated_duration_days=0
                ))

            # Build References
            references = []
            for i, ref in enumerate(old_data.get("references", [])):
                ref_id = f"{sch_id}_REF_{i+1:02d}"
                title = ref.get("title", "Reference Source")
                url = ref.get("url", "")
                
                ref_type = "third_party"
                if "official" in title.lower() or "policy" in title.lower():
                    ref_type = "official_guidelines"
                elif "portal" in title.lower() or "apply" in title.lower():
                    ref_type = "application_portal"

                references.append(Reference(
                    id=ref_id,
                    title=title,
                    url=url,
                    type=ref_type,
                    language="en"
                ))

            # Build Metadata
            last_verified = format_date(old_data.get("last_verified_date", ""))
            metadata = Metadata(
                created_at=last_verified,
                updated_at=last_verified,
                verified_at=last_verified,
                source_confidence="official",
                compiled_by="migration_bot",
                reviewed_by="admin",
                quality_score=100,
                notes=old_data.get("notes", "")
            )

            # Assemble SchemeDocument
            scheme_doc = SchemeDocument(
                schema_version="1.0.0",
                scheme=scheme_identity,
                benefits=benefits,
                eligibility_rules=eligibility_rules,
                documents=documents,
                workflow=workflow,
                references=references,
                metadata=metadata
            )

            # Validate and write back to file
            validated_dict = scheme_doc.model_dump()
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(validated_dict, f, indent=4, ensure_ascii=False)

            # print(f"Successfully migrated: {file_path.name}")
            success_count += 1

        except Exception as e:
            print(f"Failed to migrate {file_path.name}: {e}")
            import traceback
            traceback.print_exc()

    print(f"Migration completed. Success rate: {success_count}/{len(json_files)}")

if __name__ == "__main__":
    main()
