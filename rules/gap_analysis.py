from typing import Any, Dict, List
from models.scheme import SchemeDocument
from rules.engine import RulesEngine

class GapAnalysisEngine:
    """
    Engine to identify eligibility gaps and recommend hardcoded actions to become eligible.
    """
    
    ACTION_MAP = {
        "business.has_udyam_registration": {
            "action": "Register on the Udyam portal to become an official MSME.",
            "estimated_effort": "20 minutes",
            "estimated_cost": "Free",
            "impact_type": "High Impact"
        },
        "business.msme_segment": {
            "action": "Register under Udyam. If already registered, ensure your turnover/investment classification matches.",
            "estimated_effort": "20 minutes",
            "estimated_cost": "Free",
            "impact_type": "High Impact"
        },
        "business.establishment_year": {
            "action": "Maintain operations. This scheme requires a minimum business vintage. You will become eligible automatically over time.",
            "estimated_effort": "Waiting period",
            "estimated_cost": "None",
            "impact_type": "Long Term"
        },
        "business.turnover": {
            "action": "This scheme has specific turnover limits. Scaling your operations or optimizing revenue reporting may affect eligibility.",
            "estimated_effort": "Variable",
            "estimated_cost": "Variable",
            "impact_type": "Medium Impact"
        }
    }

    @classmethod
    def analyze_gaps(
        cls, 
        profile: Dict[str, Any], 
        schemes: List[SchemeDocument]
    ) -> Dict[str, Any]:
        """
        Runs eligibility checks against all schemes. 
        For schemes where the user is NOT eligible, it captures the failed rules
        and maps them to actionable recommendations.
        """
        business_dict = {"business": profile}
        
        eligible_schemes = []
        ineligible_schemes = []
        failed_rule_counts = {}
        
        potential_benefit_unlocked = 0.0
        
        for scheme in schemes:
            is_eligible = True
            scheme_failed_rules = []
            
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
                        
                if not param_exists or current_val is None:
                    # If param doesn't exist, we can't definitively say they fail, 
                    # but for gap analysis, we treat missing data as 'not currently eligible' 
                    # though normally this would trigger a question.
                    # For strict gap analysis, assume we have a complete enough profile.
                    continue
                    
                passed = RulesEngine.evaluate_rule(business_dict, param, op, val)
                if not passed:
                    is_eligible = False
                    scheme_failed_rules.append({
                        "parameter": param,
                        "operator": op,
                        "required_value": val,
                        "current_value": current_val
                    })
                    
            if is_eligible:
                eligible_schemes.append(scheme.scheme.name)
            else:
                if scheme_failed_rules:
                    ineligible_schemes.append({
                        "scheme_name": scheme.scheme.name,
                        "failed_rules": scheme_failed_rules
                    })
                    
                    # Track failures for aggregate recommendations
                    for fr in scheme_failed_rules:
                        param = fr["parameter"]
                        if param not in failed_rule_counts:
                            failed_rule_counts[param] = {
                                "count": 0, 
                                "potential_benefit": 0.0,
                                "schemes_unlocked": []
                            }
                            
                        failed_rule_counts[param]["count"] += 1
                        failed_rule_counts[param]["schemes_unlocked"].append(scheme.scheme.name)
                        
                        max_amt = max([b.max_amount for b in scheme.benefits] + [0.0])
                        failed_rule_counts[param]["potential_benefit"] += max_amt
                        potential_benefit_unlocked += max_amt

        # Generate top recommendations
        top_improvements = []
        for param, data in sorted(failed_rule_counts.items(), key=lambda x: x[1]["count"], reverse=True):
            action_data = cls.ACTION_MAP.get(param, {
                "action": f"Ensure your {param.split('.')[-1].replace('_', ' ')} meets scheme requirements.",
                "estimated_effort": "Unknown",
                "estimated_cost": "Unknown",
                "impact_type": "Medium Impact"
            })
            
            top_improvements.append({
                "parameter": param,
                "action": action_data["action"],
                "estimated_effort": action_data["estimated_effort"],
                "estimated_cost": action_data["estimated_cost"],
                "impact_type": action_data["impact_type"],
                "schemes_unlocked_count": data["count"],
                "potential_benefit_inr": data["potential_benefit"],
                "schemes": data["schemes_unlocked"]
            })
            
        total_schemes = len(schemes)
        current_eligibility = (len(eligible_schemes) / total_schemes * 100) if total_schemes else 0
        potential_eligibility = ((len(eligible_schemes) + len(ineligible_schemes)) / total_schemes * 100) if total_schemes else 0

        return {
            "current_eligibility_score": round(current_eligibility, 1),
            "potential_eligibility_score": round(potential_eligibility, 1),
            "gap_percentage": round(potential_eligibility - current_eligibility, 1),
            "total_potential_benefit_unlocked": potential_benefit_unlocked,
            "top_improvements": top_improvements
        }
