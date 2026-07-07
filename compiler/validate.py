import json
import re
from typing import List, Dict, Any
from pydantic import BaseModel, ValidationError
from models import SchemeDocument

class ValidationReport(BaseModel):
    id: str
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    score: int

def validate_document(raw_json_str: str, file_name: str = "") -> ValidationReport:
    errors = []
    warnings = []
    scheme_id = file_name or "Unknown"

    # 1. Parse JSON syntax
    try:
        data = json.loads(raw_json_str)
    except json.JSONDecodeError as je:
        errors.append(f"Invalid JSON syntax: {str(je)}")
        return ValidationReport(id=scheme_id, is_valid=False, errors=errors, warnings=warnings, score=0)

    # Resolve ID if possible
    scheme_id = data.get("scheme", {}).get("id") or scheme_id

    # 2. Run Pydantic validation
    scheme_doc = None
    try:
        scheme_doc = SchemeDocument.model_validate(data)
    except ValidationError as ve:
        for err in ve.errors():
            loc = " -> ".join(str(x) for x in err["loc"])
            errors.append(f"Field error at [{loc}]: {err['msg']}")

    # If basic schema is broken, return immediately with score 0
    if not scheme_doc:
        return ValidationReport(id=scheme_id, is_valid=False, errors=errors, warnings=warnings, score=0)

    # 3. Custom Deep Validation
    s = scheme_doc.scheme

    # Validate URLs in references
    for ref in scheme_doc.references:
        if not re.match(r"^https?://.+$", ref.url):
            errors.append(f"Reference '{ref.id}' has invalid URL: {ref.url}")

    # Validate duplicate IDs
    benefit_ids = [b.id for b in scheme_doc.benefits]
    if len(benefit_ids) != len(set(benefit_ids)):
        dup = [x for x in set(benefit_ids) if benefit_ids.count(x) > 1]
        errors.append(f"Duplicate Benefit IDs found: {dup}")

    rule_ids = [r.id for r in scheme_doc.eligibility_rules]
    if len(rule_ids) != len(set(rule_ids)):
        dup = [x for x in set(rule_ids) if rule_ids.count(x) > 1]
        errors.append(f"Duplicate Rule IDs found: {dup}")

    doc_ids = [d.id for d in scheme_doc.documents]
    if len(doc_ids) != len(set(doc_ids)):
        dup = [x for x in set(doc_ids) if doc_ids.count(x) > 1]
        errors.append(f"Duplicate Document IDs found: {dup}")

    wf_ids = [w.id for w in scheme_doc.workflow]
    if len(wf_ids) != len(set(wf_ids)):
        dup = [x for x in set(wf_ids) if wf_ids.count(x) > 1]
        errors.append(f"Duplicate Workflow Step IDs found: {dup}")

    # Circular/Looping step numbers in workflow
    step_numbers = [w.step_number for w in scheme_doc.workflow]
    if len(step_numbers) != len(set(step_numbers)):
        dup = [x for x in set(step_numbers) if step_numbers.count(x) > 1]
        warnings.append(f"Duplicate Workflow Step Numbers found: {dup}")

    # Warnings for empty sections (encouraging completeness)
    if not scheme_doc.benefits:
        warnings.append("No benefits listed for this scheme.")
    if not scheme_doc.eligibility_rules:
        warnings.append("No eligibility rules listed.")
    if not scheme_doc.documents:
        warnings.append("No required documents listed.")
    if not scheme_doc.workflow:
        warnings.append("No workflow steps listed.")
    if not scheme_doc.references:
        warnings.append("No references listed.")

    # Calculate validation score
    # Start at 100, deduct 10 for each error, 2 for each warning
    score = 100 - (len(errors) * 15) - (len(warnings) * 3)
    score = max(0, min(100, score))

    is_valid = len(errors) == 0

    return ValidationReport(
        id=s.id,
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        score=score
    )
