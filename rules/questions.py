from typing import Any, Dict, List, Tuple
from rules.engine import RulesEngine
from models.scheme import SchemeDocument

# Hardcoded mapping of parameters to natural language questions
PARAMETER_QUESTIONS = {
    "business.msme_segment": "Are you registered as a Micro, Small, or Medium Enterprise (MSME)?",
    "business.turnover": "What is your approximate annual turnover (in INR)?",
    "business.state": "In which state is your business operating?",
    "business.district": "In which district is your business operating?",
    "business.sector": "What is the primary sector of your business (e.g., manufacturing, services, agriculture_allied)?",
    "business.ownership_category": "Does the ownership fall under any special category (e.g., women, SC, ST)?",
    "business.constitution": "What is your business constitution (e.g., proprietorship, private_limited)?",
    "business.investment_plant_machinery": "What is your total investment in plant and machinery (in INR)?",
    "business.establishment_year": "In what year was your business established?",
    "business.has_udyam_registration": "Do you have an Udyam Registration Certificate?",
    "business.employment_count": "How many employees do you currently have?",
    "business.export_status": "Do you export goods or services?"
}

class QuestionEngine:
    @staticmethod
    def get_next_best_question(
        profile: Dict[str, Any], 
        candidate_schemes: List[SchemeDocument]
    ) -> Dict[str, Any]:
        """
        Determines the next best question to ask based on information gain.
        1. Filters candidates that are already ineligible.
        2. Finds missing parameters in the remaining candidates.
        3. Returns the parameter that appears most frequently (simplistic info gain).
        """
        business_dict = {"business": profile}
        
        valid_candidates = []
        missing_parameters = {}
        
        for scheme in candidate_schemes:
            is_valid = True
            scheme_missing_params = set()
            
            for rule in scheme.eligibility_rules:
                param = rule.parameter.value if hasattr(rule.parameter, "value") else str(rule.parameter)
                op = rule.operator.value if hasattr(rule.operator, "value") else str(rule.operator)
                val = rule.value
                
                # Check if param exists in profile
                parts = param.split('.')
                current_val = business_dict
                param_exists = True
                for p in parts:
                    if isinstance(current_val, dict) and p in current_val:
                        current_val = current_val[p]
                    else:
                        param_exists = False
                        break
                
                if param_exists and current_val is not None:
                    # Parameter is known, evaluate rule
                    passed = RulesEngine.evaluate_rule(business_dict, param, op, val)
                    if not passed:
                        is_valid = False
                        break # Scheme is invalid, skip remaining rules
                else:
                    # Parameter is missing
                    scheme_missing_params.add(param)
            
            if is_valid:
                valid_candidates.append(scheme)
                for missing_param in scheme_missing_params:
                    missing_parameters[missing_param] = missing_parameters.get(missing_param, 0) + 1
                    
        if not valid_candidates or not missing_parameters:
            return {"status": "complete", "message": "No more questions needed."}
            
        # Find the parameter that splits the candidate space the most (highest frequency)
        best_param = max(missing_parameters.items(), key=lambda x: x[1])[0]
        
        question_text = PARAMETER_QUESTIONS.get(
            best_param, 
            f"What is your {best_param.split('.')[-1].replace('_', ' ')}?"
        )
        
        return {
            "status": "question",
            "parameter": best_param,
            "question": question_text,
            "candidates_remaining": len(valid_candidates)
        }
