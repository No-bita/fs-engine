from typing import List, Dict, Any
from models.scheme import SchemeDocument

class IntentClassifier:
    """
    A lightweight, deterministic classifier to map natural language queries 
    into predefined, structured business intents.
    """
    
    INTENT_MAPPINGS = {
        "working capital": ["working capital support", "working_capital", "operating expenses", "day-to-day"],
        "machinery": ["machinery purchase", "equipment financing", "plant", "manufacturing setup"],
        "expansion": ["business expansion", "new factory", "growth"],
        "export": ["export finance", "global market", "international trade"],
        "solar": ["solar", "green technology funding", "energy efficiency", "renewable"],
        "women": ["women_owned", "hiring women employees", "women empowerment"],
        "agriculture": ["farming capital", "crop cultivation", "need loan"],
    }
    
    @classmethod
    def classify_intent(cls, user_query: str) -> Dict[str, Any]:
        """
        Classifies the user query into structured intents using keyword heuristics.
        Returns the primary intent and confidence score.
        """
        query_lower = user_query.lower()
        matched_intents = set()
        
        for primary_intent, keywords in cls.INTENT_MAPPINGS.items():
            if primary_intent in query_lower:
                matched_intents.add(primary_intent)
            for keyword in keywords:
                if keyword in query_lower:
                    matched_intents.add(primary_intent)
                    # Also map to the specific scheme tag if applicable
                    matched_intents.add(keyword.replace(' ', '_'))
                    
        # In a real scenario, this would use a lightweight LLM or embedding model.
        if not matched_intents:
            return {
                "status": "clarification_needed",
                "message": "Could you clarify what kind of financial support you're looking for? (e.g., working capital, machinery purchase, business expansion)",
                "confidence": 0.0,
                "intents": []
            }
            
        return {
            "status": "success",
            "confidence": 0.85, # Mock confidence for rule-based matching
            "intents": list(matched_intents)
        }

    @classmethod
    def filter_schemes_by_intent(cls, intents: List[str], schemes: List[SchemeDocument]) -> List[SchemeDocument]:
        """
        Filters candidate schemes based on the classified intents.
        """
        if not intents:
            return schemes
            
        filtered = []
        intents_lower = [i.lower() for i in intents]
        for s in schemes:
            scheme_intents = [si.lower() for si in s.scheme.tags.business_intents]
            # Check for intersection
            if any(intent in scheme_intents for intent in intents_lower):
                filtered.append(s)
                continue
                
            # Fallback: check search_keywords
            scheme_keywords = [sk.lower() for sk in s.scheme.tags.search_keywords]
            if any(intent in scheme_keywords for intent in intents_lower):
                filtered.append(s)
                
        return filtered
