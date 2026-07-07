import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from backend.main import recommend_schemes
from models import BusinessProfile

def main():
    test_file = project_root / "tests" / "regression_profiles.json"
    if not test_file.exists():
        print(f"Regression profiles file {test_file} not found.")
        sys.exit(1)

    with open(test_file, "r", encoding="utf-8") as f:
        profiles = json.load(f)

    print(f"--- Running {len(profiles)} Regression Tests ---")

    passed_count = 0
    failed_count = 0

    for item in profiles:
        prof_id = item["id"]
        desc = item["description"]
        prof_data = item["profile"]
        expected = item["expected_schemes"]

        profile = BusinessProfile(**prof_data)
        recommended = recommend_schemes(profile)
        recommended_ids = [s.scheme.scheme.id for s in recommended]

        # Check if all expected scheme IDs are matching
        mismatched = []
        for exp in expected:
            if exp not in recommended_ids:
                mismatched.append(exp)

        if not mismatched:
            print(f"✅ {prof_id} - {desc} | PASSED")
            passed_count += 1
        else:
            print(f"❌ {prof_id} - {desc} | FAILED")
            print(f"   Expected: {expected}")
            print(f"   Received: {recommended_ids}")
            print(f"   Missing matches: {mismatched}")
            failed_count += 1

    print("\n--- Regression Test Summary ---")
    print(f"Total Tests Run: {len(profiles)}")
    print(f"Passed: {passed_count}")
    print(f"Failed: {failed_count}")

    if failed_count > 0:
        print("🚨 Some regression tests failed!")
        sys.exit(1)
    else:
        print("🎉 All regression tests passed successfully!")
        sys.exit(0)

if __name__ == "__main__":
    main()
