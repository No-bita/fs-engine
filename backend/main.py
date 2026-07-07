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
    # Load canonical schemes directly from local JSON files to serve requests
    json_dir = Path("/Users/aaryanshah/Downloads/FS Engine/data/json")
    schemes = []
    if json_dir.exists():
        for file in json_dir.glob("*.json"):
            if file.name.startswith("_"):
                continue
            try:
                with open(file, "r", encoding="utf-8") as f:
                    scheme_doc = SchemeDocument.model_validate_json(f.read())
                    schemes.append(scheme_doc)
            except Exception as e:
                print(f"Error validating/loading {file.name}: {e}")
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

@app.post("/api/scheme/{scheme_id}/rules")
def save_scheme_rules(scheme_id: str, payload: SaveRulesRequest):
    schemes_dir = Path("/Users/aaryanshah/Downloads/FS Engine/data/json")
    target_file = None
    for file in schemes_dir.glob("*.json"):
        if file.name.startswith("_"):
            continue
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("scheme", {}).get("id") == scheme_id:
                    target_file = file
                    break
        except Exception:
            continue
            
    if not target_file:
        raise HTTPException(status_code=404, detail="Scheme not found in registry")
        
    try:
        with open(target_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        data["eligibility_rules"] = payload.rules
        
        with open(target_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        from compiler.compile import compile_registry
        compile_registry(schemes_dir, schemes_dir)
        
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
