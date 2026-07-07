from typing import Any, Dict, List

class RulesEngine:
    @staticmethod
    def evaluate_rule(business_profile: Dict[str, Any], parameter: Any, operator: Any, rule_value: Any) -> bool:
        # Resolve the business parameter nested path (e.g., 'business.turnover')
        param_str = parameter.value if hasattr(parameter, "value") else str(parameter)
        parts = param_str.split('.')
        current_val = business_profile
        for p in parts:
            if isinstance(current_val, dict) and p in current_val:
                current_val = current_val[p]
            elif hasattr(current_val, p):
                current_val = getattr(current_val, p)
            else:
                # Parameter not found in business profile
                return False

        # Apply operators
        op = operator.value if hasattr(operator, "value") else str(operator).upper()
        
        try:
            if op == "=":
                return current_val == rule_value
            elif op == "!=":
                return current_val != rule_value
            elif op == ">":
                return float(current_val) > float(rule_value)
            elif op == "<":
                return float(current_val) < float(rule_value)
            elif op == ">=":
                return float(current_val) >= float(rule_value)
            elif op == "<=":
                return float(current_val) <= float(rule_value)
            elif op == "IN":
                if isinstance(rule_value, list):
                    return current_val in rule_value
                return current_val in [rule_value]
            elif op == "NOT IN":
                if isinstance(rule_value, list):
                    return current_val not in rule_value
                return current_val not in [rule_value]
            elif op == "BETWEEN":
                # Expect rule_value to be a list/tuple of [min, max]
                return float(rule_value[0]) <= float(current_val) <= float(rule_value[1])
            elif op == "CONTAINS":
                if isinstance(current_val, list):
                    return rule_value in current_val
                return str(rule_value) in str(current_val)
        except Exception:
            return False

        return False

    @classmethod
    def check_eligibility(cls, business_profile: Dict[str, Any], eligibility_rules: List[Any]) -> bool:
        for rule in eligibility_rules:
            if hasattr(rule, "parameter"):
                param = rule.parameter
                op = rule.operator
                val = rule.value
            elif isinstance(rule, dict):
                param = rule.get("parameter")
                op = rule.get("operator")
                val = rule.get("value")
            else:
                continue
                
            if not cls.evaluate_rule(business_profile, param, op, val):
                return False
        return True
