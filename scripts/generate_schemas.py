import json
import sys
from pathlib import Path

# Add project root to path so we can import models
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from models import (
    SchemeDocument, Benefit, EligibilityRule, DocumentRequirement,
    WorkflowStep, BusinessProfile, Reference
)

def save_schema(model_cls, filename: str):
    schema = model_cls.model_json_schema()
    output_path = project_root / "schemas" / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=4, ensure_ascii=False)
    print(f"Generated {filename} at {output_path}")

def main():
    save_schema(SchemeDocument, "scheme.schema.json")
    save_schema(Benefit, "benefit.schema.json")
    save_schema(EligibilityRule, "eligibility-rule.schema.json")
    save_schema(DocumentRequirement, "document.schema.json")
    save_schema(WorkflowStep, "workflow.schema.json")
    save_schema(BusinessProfile, "business.schema.json")
    save_schema(Reference, "reference.schema.json")

if __name__ == "__main__":
    main()
