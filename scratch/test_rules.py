import unittest
from rules.engine import RulesEngine

class TestRulesEngine(unittest.TestCase):
    def test_numeric_comparison(self):
        profile = {"business": {"turnover": 450000000}}
        
        # Test <= operator (True)
        rule_ok = {"parameter": "business.turnover", "operator": "<=", "value": 500000000}
        self.assertTrue(RulesEngine.check_eligibility(profile, [rule_ok]))
        
        # Test <= operator (False)
        rule_fail = {"parameter": "business.turnover", "operator": "<=", "value": 300000000}
        self.assertFalse(RulesEngine.check_eligibility(profile, [rule_fail]))

    def test_in_comparison(self):
        profile = {"business": {"msme_segment": "micro"}}
        
        # Test IN operator (True)
        rule_ok = {"parameter": "business.msme_segment", "operator": "IN", "value": ["micro", "small"]}
        self.assertTrue(RulesEngine.check_eligibility(profile, [rule_ok]))
        
        # Test IN operator (False)
        rule_fail = {"parameter": "business.msme_segment", "operator": "IN", "value": ["medium"]}
        self.assertFalse(RulesEngine.check_eligibility(profile, [rule_fail]))

if __name__ == "__main__":
    unittest.main()
