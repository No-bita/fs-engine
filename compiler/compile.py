import os
import json
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from compiler.normalize import normalize_dict
from compiler.enrich import enrich_metadata_and_tags
from compiler.quality import calculate_quality_score
from compiler.validate import validate_document, ValidationReport
from compiler.lint import lint_document, LintIssue

def compile_registry(source_dir: Path, output_dir: Path):
    if not source_dir.exists():
        print(f"Source directory {source_dir} not found.")
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    json_files = [f for f in source_dir.glob("*.json") if not f.name.startswith("_")]

    print(f"--- Starting Compilation Pipeline for {len(json_files)} schemes ---")

    all_reports: List[Dict[str, Any]] = []
    failed_compilation = 0

    for file_path in json_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)

            # 1. Normalize
            normalized = normalize_dict(raw_data)

            # 2. Enrich (Keywords, FAQs, and Atomic Rules Completeness)
            enriched = enrich_metadata_and_tags(normalized)

            # 3. Calculate and inject Quality Score
            quality_score = calculate_quality_score(enriched)
            if "metadata" in enriched:
                enriched["metadata"]["quality_score"] = quality_score

            # Serialize temporarily to validate
            temp_json_str = json.dumps(enriched, ensure_ascii=False)

            # 4. Validate
            report: ValidationReport = validate_document(temp_json_str, file_name=file_path.name)

            # 5. Lint
            lint_issues: List[LintIssue] = lint_document(enriched)

            # Write compiled file back to output
            out_file_path = output_dir / file_path.name
            with open(out_file_path, "w", encoding="utf-8") as out_f:
                json.dump(enriched, out_f, indent=4, ensure_ascii=False)

            # Print status
            status_symbol = "✅" if report.is_valid else "❌"
            lint_symbols = "⚠️" if lint_issues else ""
            print(f"{status_symbol} {file_path.name} | Score: {report.score} | Quality: {quality_score} {lint_symbols}")

            if not report.is_valid:
                failed_compilation += 1
                for err in report.errors:
                    print(f"   [Error] {err}")

            for issue in lint_issues:
                sev_icon = "🛑" if issue.severity == "error" else "💡"
                print(f"   [Lint {issue.severity}] {sev_icon} ({issue.category}): {issue.message}")

            all_reports.append({
                "file_name": file_path.name,
                "scheme_id": report.id,
                "is_valid": report.is_valid,
                "score": report.score,
                "quality_score": quality_score,
                "errors": report.errors,
                "warnings": report.warnings,
                "lint_issues": [issue.to_dict() for issue in lint_issues]
            })

        except Exception as e:
            print(f"🚨 Failed to compile {file_path.name}: {e}")
            import traceback
            traceback.print_exc()
            failed_compilation += 1

    print("\n--- Compilation Pipeline Completed ---")
    print(f"Total schemes compiled: {len(json_files)}")
    print(f"Validation failures: {failed_compilation}")
    
    # Save a global compilation report
    report_path = output_dir / "_compilation_report.json"
    with open(report_path, "w", encoding="utf-8") as rep_f:
        json.dump(all_reports, rep_f, indent=4, ensure_ascii=False)
    print(f"Global compilation report saved to {report_path}")

def main():
    source_dir = project_root / "data" / "json"
    # We compile in-place to enrich and clean up the active registry
    compile_registry(source_dir, source_dir)

if __name__ == "__main__":
    main()
