import os
import json
import psycopg2
import sys
from pathlib import Path

# Add project root to path so we can import models
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from models import SchemeDocument

# Database connection setup from Env
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("DB_NAME", "msme_db")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASS = os.environ.get("DB_PASS", "postgres")
DB_PORT = os.environ.get("DB_PORT", "5432")

def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT
    )

def seed_database():
    json_dir = Path("/Users/aaryanshah/Downloads/FS Engine/data/json")
    if not json_dir.exists():
        print(f"Directory {json_dir} does not exist.")
        return

    conn = get_connection()
    cur = conn.cursor()

    try:
        # Load and execute schema.sql
        schema_path = Path("/Users/aaryanshah/Downloads/FS Engine/backend/schema.sql")
        with open(schema_path, "r", encoding="utf-8") as schema_file:
            cur.execute(schema_file.read())
        conn.commit()
        print("Schema successfully initialized.")

        for json_file in json_dir.glob("*.json"):
            with open(json_file, "r", encoding="utf-8") as f:
                scheme_doc = SchemeDocument.model_validate_json(f.read())

            s = scheme_doc.scheme
            meta = scheme_doc.metadata

            # Insert scheme
            cur.execute("""
                INSERT INTO schemes (
                    id, name, short_name, slug, description, scheme_type,
                    provider_category, provider_name, provider_government_level,
                    geography_coverage, geography_states, geography_districts,
                    business_stages, sectors, benefit_categories, msme_segments, business_intents,
                    status, priority, created_at, updated_at, verified_at,
                    source_confidence, compiled_by, reviewed_by, quality_score, notes
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                s.id, s.name, s.short_name, s.slug, s.description, s.scheme_type.value,
                s.provider.category.value, s.provider.name, s.provider.government_level.value,
                s.geography.coverage.value, s.geography.states, s.geography.districts,
                s.tags.business_stages, s.tags.sectors, s.tags.benefit_categories, s.tags.msme_segments, s.tags.business_intents,
                s.status.value, s.priority.value, meta.created_at, meta.updated_at, meta.verified_at,
                meta.source_confidence.value, meta.compiled_by, meta.reviewed_by, meta.quality_score, meta.notes
            ))

            # Insert benefits
            for b in scheme_doc.benefits:
                cur.execute("""
                    INSERT INTO benefits (
                        id, scheme_id, name, category, summary,
                        benefit_calculation_logic, max_amount, min_amount,
                        loan_range, interest_rate, collateral_required, collateral_details,
                        guarantee_coverage, tenure_months, moratorium_months, margin_contribution
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    b.id, s.id, b.name, b.category.value, b.summary,
                    b.calculation_logic, b.max_amount, b.min_amount,
                    b.loan_range, b.interest_rate, b.collateral_required, b.collateral_details,
                    b.guarantee_coverage, b.tenure_months, b.moratorium_months, b.margin_contribution
                ))

            # Insert eligibility rules
            for r in scheme_doc.eligibility_rules:
                cur.execute("""
                    INSERT INTO eligibility_rules (id, scheme_id, parameter, operator, value)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    r.id, s.id, r.parameter.value, r.operator.value, json.dumps(r.value)
                ))

            # Insert documents
            for d in scheme_doc.documents:
                cur.execute("""
                    INSERT INTO documents (id, scheme_id, name, description, is_mandatory, issuing_authority, digitized_verification_available)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    d.id, s.id, d.name, d.description, d.is_mandatory, d.issuing_authority, d.digitized_verification_available
                ))

            # Insert workflow
            for w in scheme_doc.workflow:
                cur.execute("""
                    INSERT INTO workflow (id, scheme_id, step_number, name, description, actor, channel, url, estimated_duration_days)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    w.id, s.id, w.step_number, w.name, w.description, w.actor.value, w.channel.value, w.url, w.estimated_duration_days
                ))

            # Insert references
            for ref in scheme_doc.references:
                cur.execute("""
                    INSERT INTO "references" (id, scheme_id, title, url, type, language)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    ref.id, s.id, ref.title, ref.url, ref.type.value, ref.language
                ))

        conn.commit()
        print("Database seed completed successfully.")

    except Exception as e:
        conn.rollback()
        print(f"Error seeding database: {e}")
    finally:
        try:
            cur.close()
            conn.close()
        except Exception:
            pass

if __name__ == "__main__":
    seed_database()
