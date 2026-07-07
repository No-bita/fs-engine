from typing import Dict, Any

def calculate_quality_score(data: Dict[str, Any]) -> int:
    """
    Computes a weighted quality score out of 100.
    - Metadata: 20 points
    - Benefits: 20 points
    - Rules: 20 points
    - Workflow: 20 points
    - Documents: 20 points
    """
    if not isinstance(data, dict):
        return 0

    metadata_pts = 0
    benefits_pts = 0
    rules_pts = 0
    workflow_pts = 0
    documents_pts = 0

    # 1. Metadata completeness (Max 20)
    meta = data.get("metadata", {})
    if isinstance(meta, dict):
        if meta.get("notes"): metadata_pts += 4
        if meta.get("verified_at"): metadata_pts += 4
        if meta.get("compiled_by"): metadata_pts += 4
        if meta.get("reviewed_by"): metadata_pts += 4
        if meta.get("source_confidence"): metadata_pts += 4

    # 2. Benefits completeness (Max 20)
    benefits = data.get("benefits", [])
    if isinstance(benefits, list) and len(benefits) > 0:
        benefits_pts += 10
        first_ben = benefits[0]
        if isinstance(first_ben, dict):
            if first_ben.get("calculation_logic"): benefits_pts += 5
            if first_ben.get("summary"): benefits_pts += 5

    # 3. Rules completeness (Max 20)
    rules = data.get("eligibility_rules", [])
    if isinstance(rules, list) and len(rules) > 0:
        rules_pts += 10
        # If rules have defined fields
        first_rule = rules[0]
        if isinstance(first_rule, dict):
            if first_rule.get("parameter") and first_rule.get("operator") and "value" in first_rule:
                rules_pts += 10

    # 4. Workflow completeness (Max 20)
    workflow = data.get("workflow", [])
    if isinstance(workflow, list) and len(workflow) > 0:
        workflow_pts += 10
        if len(workflow) >= 2:
            workflow_pts += 10
        else:
            workflow_pts += 5

    # 5. Documents completeness (Max 20)
    documents = data.get("documents", [])
    if isinstance(documents, list) and len(documents) > 0:
        documents_pts += 10
        # At least one document is mandatory or described
        first_doc = documents[0]
        if isinstance(first_doc, dict):
            if first_doc.get("is_mandatory") is True or first_doc.get("description"):
                documents_pts += 10

    total_score = metadata_pts + benefits_pts + rules_pts + workflow_pts + documents_pts
    return total_score
