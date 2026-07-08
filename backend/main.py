import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from typing import List, Optional, Dict, Any
import json
from pathlib import Path
from pydantic import BaseModel, Field
from rules.engine import RulesEngine
from rules.nlp import IntentClassifier
from rules.questions import QuestionEngine
from rules.gap_analysis import GapAnalysisEngine
from models import SchemeDocument, BusinessProfile
import firebase_admin
from firebase_admin import credentials, firestore
from compiler.normalize import normalize_dict
from compiler.enrich import enrich_metadata_and_tags
from compiler.quality import calculate_quality_score
from compiler.validate import validate_document
import os

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    cred_path = project_root / "FS Engine Firebase Admin SDK.json"
    if cred_path.exists():
        cred = credentials.Certificate(str(cred_path))
        firebase_admin.initialize_app(cred)
    elif "FIREBASE_SERVICE_ACCOUNT" in os.environ:
        cred = credentials.Certificate(json.loads(os.environ["FIREBASE_SERVICE_ACCOUNT"]))
        firebase_admin.initialize_app(cred)
    else:
        firebase_admin.initialize_app()

db = firestore.client()

app = FastAPI(title="MSME Benefits Platform API", version="1.0.0")

class RuleEvaluationResult(BaseModel):
    rule_id: str
    parameter: str
    operator: str
    value: Any
    passed: bool
    explanation: str

class RecommendationResponse(BaseModel):
    scheme: SchemeDocument
    score: float
    is_eligible: bool
    rule_evaluations: List[RuleEvaluationResult]

def load_local_schemes() -> List[SchemeDocument]:
    # Fetch from Firestore instead of local files
    schemes = []
    docs = db.collection("schemes").stream()
    for doc in docs:
        try:
            scheme_doc = SchemeDocument.model_validate(doc.to_dict())
            schemes.append(scheme_doc)
        except Exception as e:
            print(f"Error validating {doc.id}: {e}")
    return schemes

@app.get("/dashboard", response_class=HTMLResponse)
def get_dashboard():
    # Serve the premium HTML dashboard
    html_path = Path("/Users/aaryanshah/Downloads/FS Engine/backend/dashboard/index.html")
    if html_path.exists():
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Dashboard HTML File Not Found</h1>", status_code=404)

@app.get("/api/diagnostics")
def get_diagnostics():
    # Read global compilation report containing quality scores, validate reports and lint issues
    report_path = Path("/Users/aaryanshah/Downloads/FS Engine/data/json/_compilation_report.json")
    if report_path.exists():
        with open(report_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

@app.post("/business")
def save_business_profile(profile: BusinessProfile):
    # Endpoint to save or structure business details
    return {"status": "success", "profile": profile}

@app.get("/search", response_model=List[SchemeDocument])
def search_schemes(q: Optional[str] = None):
    # Basic search filter over canonical schemes metadata
    schemes = load_local_schemes()
    if not q:
        return schemes
    
    query = q.lower()
    filtered = []
    for s in schemes:
        name = s.scheme.name.lower()
        provider = s.scheme.provider.name.lower()
        notes = s.metadata.notes.lower() if s.metadata.notes else ""
        
        if query in name or query in provider or query in notes:
            filtered.append(s)
            
    return filtered

@app.post("/recommend", response_model=List[RecommendationResponse])
def recommend_schemes(profile: BusinessProfile):
    schemes = load_local_schemes()
    results = []
    
    business_dict = {"business": profile.model_dump()}
    
    for s in schemes:
        rules = s.eligibility_rules
        is_eligible = True
        rule_evaluations = []
        
        # 1. Evaluate Eligibility Rules
        for r in rules:
            param = r.parameter.value if hasattr(r.parameter, "value") else str(r.parameter)
            op = r.operator.value if hasattr(r.operator, "value") else str(r.operator)
            val = r.value
            
            passed = RulesEngine.evaluate_rule(business_dict, r.parameter, r.operator, r.value)
            if not passed:
                is_eligible = False
            
            rule_evaluations.append(RuleEvaluationResult(
                rule_id=r.id,
                parameter=param,
                operator=op,
                value=val,
                passed=passed,
                explanation=f"{'Passed' if passed else 'Failed'}: {param.split('.')[-1]} {op} {val} (Business value: {business_dict['business'].get(param.split('.')[-1])})"
            ))
            
        # 2. Compute Recommendation Match Score
        # Benefit Score (max 20)
        max_amt = max([b.max_amount for b in s.benefits] + [0.0])
        if max_amt >= 5000000.0: benefit_score = 20.0
        elif max_amt >= 1000000.0: benefit_score = 15.0
        elif max_amt >= 100000.0: benefit_score = 10.0
        else: benefit_score = 5.0
        
        # Intent / Tag overlap score (max 20)
        sector_match = 10.0 if profile.sector in s.scheme.tags.sectors else 0.0
        segment_match = 10.0 if profile.msme_segment in s.scheme.tags.msme_segments else 0.0
        intent_score = sector_match + segment_match
        
        # Ease score (max 20)
        doc_count = len(s.documents)
        if doc_count <= 3: ease_score = 20.0
        elif doc_count <= 5: ease_score = 15.0
        else: ease_score = 10.0
        
        # Priority score (max 20)
        prio = s.scheme.priority.value if hasattr(s.scheme.priority, "value") else str(s.scheme.priority)
        if prio == "tier_1": priority_score = 20.0
        elif prio == "tier_2": priority_score = 15.0
        else: priority_score = 10.0
        
        # Quality score (max 20)
        quality_score = float(s.metadata.quality_score or 100.0) / 5.0
        
        total_score = benefit_score + intent_score + ease_score + priority_score + quality_score
        
        results.append(RecommendationResponse(
            scheme=s,
            score=total_score,
            is_eligible=is_eligible,
            rule_evaluations=rule_evaluations
        ))
        
    # Sort eligible schemes first, ranked by score descending
    results.sort(key=lambda x: (x.is_eligible, x.score), reverse=True)
    return results

@app.get("/scheme/{identifier}", response_model=SchemeDocument)
def get_scheme(identifier: str):
    schemes = load_local_schemes()
    query = identifier.lower().strip()
    for s in schemes:
        if (s.scheme.slug.lower() == query or 
            s.scheme.id.lower() == query or 
            s.scheme.name.lower() == query or 
            s.scheme.short_name.lower() == query):
            return s
    raise HTTPException(status_code=404, detail="Scheme not found")

class SaveRulesRequest(BaseModel):
    rules: List[Dict[str, Any]]
    manual_rules: List[str] = []

class SaveSchemeRequest(BaseModel):
    document: Dict[str, Any]

@app.post("/api/scheme/{scheme_id}")
def save_scheme(scheme_id: str, payload: SaveSchemeRequest):
    doc_ref = db.collection("schemes").document(scheme_id)
    doc = doc_ref.get()
    
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Scheme not found in registry")
        
    try:
        data = payload.document
        
        # Run compiler pipeline in-memory
        normalized = normalize_dict(data)
        # enriched = enrich_metadata_and_tags(normalized)
        enriched = normalized
        quality_score = calculate_quality_score(enriched)
        if "metadata" in enriched:
            enriched["metadata"]["quality_score"] = quality_score
            
        # Validate
        temp_json_str = json.dumps(enriched, ensure_ascii=False)
        report = validate_document(temp_json_str, file_name=scheme_id)
        if not report.is_valid:
            raise Exception(f"Validation failed: {report.errors}")
            
        # Update Firestore
        doc_ref.set(enriched)
        
        return {"status": "success", "message": f"Successfully updated scheme {scheme_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scheme/{scheme_id}/rules")
def save_scheme_rules(scheme_id: str, payload: SaveRulesRequest):
    doc_ref = db.collection("schemes").document(scheme_id)
    doc = doc_ref.get()
    
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Scheme not found in registry")
        
    try:
        data = doc.to_dict()
        data["eligibility_rules"] = payload.rules
        data["manual_eligibility_rules"] = payload.manual_rules
        
        # Run compiler pipeline in-memory
        normalized = normalize_dict(data)
        # enriched = enrich_metadata_and_tags(normalized)
        enriched = normalized
        quality_score = calculate_quality_score(enriched)
        if "metadata" in enriched:
            enriched["metadata"]["quality_score"] = quality_score
            
        # Validate
        temp_json_str = json.dumps(enriched, ensure_ascii=False)
        report = validate_document(temp_json_str, file_name=scheme_id)
        if not report.is_valid:
            raise Exception(f"Validation failed: {report.errors}")
            
        # Update Firestore
        doc_ref.set(enriched)
        
        return {"status": "success", "message": f"Successfully updated rules for {scheme_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/apply")
def apply_scheme(scheme_name: str, business_details: Dict[str, Any]):
    return {
        "status": "application_initiated",
        "scheme": scheme_name,
        "next_steps": "Please refer to the application_channel workflow."
    }

@app.post("/chat")
def chatbot_interaction(message: str, history: List[Dict[str, str]]):
    return {
        "reply": f"Based on your query '{message}', you can try calling the `/recommend` endpoint with your business turnover and segment details."
    }

class IntentRequest(BaseModel):
    query: str

@app.post("/api/chat/intent")
def get_intent(req: IntentRequest):
    return IntentClassifier.classify_intent(req.query)

class QuestionRequest(BaseModel):
    profile: Dict[str, Any]
    intents: List[str]

@app.post("/api/chat/question")
def get_dynamic_question(req: QuestionRequest):
    schemes = load_local_schemes()
    filtered_schemes = IntentClassifier.filter_schemes_by_intent(req.intents, schemes)
    return QuestionEngine.get_next_best_question(req.profile, filtered_schemes)

@app.post("/api/gap_analysis")
def get_gap_analysis(profile: BusinessProfile):
    schemes = load_local_schemes()
    return GapAnalysisEngine.analyze_gaps(profile.model_dump(), schemes)

@app.get("/api/audit/schemes")
def audit_schemes():
    from rules.questions import PARAMETER_QUESTIONS
    schemes = load_local_schemes()
    
    audit_data = []
    for s in schemes:
        rules = []
        raw_rules = []
        questions = []
        for r in s.eligibility_rules:
            param = r.parameter.value if hasattr(r.parameter, "value") else str(r.parameter)
            op = r.operator.value if hasattr(r.operator, "value") else str(r.operator)
            
            raw_rules.append({
                "id": r.id,
                "parameter": param,
                "operator": op,
                "value": r.value
            })
            rules.append(f"{param} {op} {r.value}")
            
            if param in PARAMETER_QUESTIONS and PARAMETER_QUESTIONS[param] not in questions:
                questions.append(PARAMETER_QUESTIONS[param])
                
        steps = []
        urls = []
        
        if s.workflow and hasattr(s.workflow, "steps"):
            for step in s.workflow.steps:
                steps.append(step.description)
                if hasattr(step, "url") and step.url:
                    urls.append(step.url)
                    
        if s.references:
            for ref in s.references:
                if hasattr(ref, "url") and ref.url and ref.url not in urls:
                    urls.append(ref.url)
                
        audit_data.append({
            "id": s.scheme.id,
            "name": s.scheme.name,
            "provider": s.scheme.provider.name,
            "description": s.scheme.description,
            "eligibility_requirements": rules,
            "raw_eligibility_rules": raw_rules,
            "questions_to_ask": questions,
            "steps_to_apply": steps,
            "urls": urls,
            "full_document": s.model_dump()
        })
        
    return audit_data

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
