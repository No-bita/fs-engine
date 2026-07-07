from typing import List, Dict, Any

class LintIssue:
    def __init__(self, category: str, message: str, severity: str = "warning"):
        self.category = category
        self.message = message
        self.severity = severity  # "error" or "warning"

    def to_dict(self) -> Dict[str, str]:
        return {
            "category": self.category,
            "message": self.message,
            "severity": self.severity
        }

def lint_document(data: Dict[str, Any]) -> List[LintIssue]:
    issues = []
    if not isinstance(data, dict):
        issues.append(LintIssue("structure", "Document is not a valid JSON object", "error"))
        return issues

    scheme = data.get("scheme", {})
    rules = data.get("eligibility_rules", [])
    benefits = data.get("benefits", [])
    documents = data.get("documents", [])
    references = data.get("references", [])

    # 1. Conflicting Rules Check
    # E.g. turnover < X and turnover > Y where X < Y (impossible range)
    turnover_rules = [r for r in rules if r.get("parameter") == "business.turnover"]
    if len(turnover_rules) >= 2:
        # Check simple conflicts
        less_than = None
        greater_than = None
        for r in turnover_rules:
            op = r.get("operator", "")
            val = r.get("value")
            try:
                val_num = float(val)
                if op in ("<", "<="):
                    less_than = min(less_than, val_num) if less_than is not None else val_num
                elif op in (">", ">="):
                    greater_than = max(greater_than, val_num) if greater_than is not None else val_num
            except (ValueError, TypeError):
                pass
        
        if less_than is not None and greater_than is not None:
            if greater_than > less_than:
                issues.append(LintIssue(
                    "rules",
                    f"Conflicting turnover rules: turnover must be > {greater_than} and < {less_than} simultaneously (impossible range).",
                    "error"
                ))

    # 2. Duplicate Rules Check
    seen_rules = set()
    for r in rules:
        param = r.get("parameter")
        op = r.get("operator")
        val = str(r.get("value"))
        rule_key = (param, op, val)
        if rule_key in seen_rules:
            issues.append(LintIssue("rules", f"Duplicate rule found: parameter={param}, operator={op}, value={val}", "warning"))
        else:
            seen_rules.add(rule_key)

    # 3. Benefits without Calculation Logic
    for b in benefits:
        if not b.get("calculation_logic") or str(b.get("calculation_logic")).strip().lower() in ("unknown", "none", "not_applicable", ""):
            issues.append(LintIssue("benefits", f"Benefit '{b.get('id')}' is missing calculation logic", "warning"))

    # 4. Inconsistent Taxonomy in Tags vs Rules
    # E.g. sector is "trading" in tags but rule uses "manufacturing"
    tag_sectors = scheme.get("tags", {}).get("sectors", [])
    for r in rules:
        if r.get("parameter") == "business.sector":
            op = r.get("operator", "")
            val = r.get("value")
            rule_sectors = [val] if isinstance(val, str) else (val if isinstance(val, list) else [])
            for rs in rule_sectors:
                if tag_sectors and rs not in tag_sectors:
                    issues.append(LintIssue(
                        "taxonomy",
                        f"Rule sector '{rs}' is not listed in scheme.tags.sectors: {tag_sectors}",
                        "warning"
                    ))

    # 5. Missing Document Requirements
    if not documents:
        issues.append(LintIssue("documents", "No document requirements specified", "warning"))

    # 6. Invalid Reference Links
    for ref in references:
        url = ref.get("url", "")
        if not url.startswith("http"):
            issues.append(LintIssue("references", f"Reference '{ref.get('id')}' has invalid URL: {url}", "error"))

    return issues
