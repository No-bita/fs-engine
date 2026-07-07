import re
from typing import Any, Dict, List

# Normalization Mappings
OWNERSHIP_MAPPING = {
    "sc": "scheduled_caste",
    "st": "scheduled_tribe",
    "scheduled caste": "scheduled_caste",
    "scheduled tribe": "scheduled_tribe",
    "sc/st": "scheduled_caste_or_tribe",
    "obc": "obc",
    "other backward class": "obc",
    "women": "women",
    "woman": "women",
    "female": "women",
    "general": "general",
    "gen": "general"
}

SECTOR_MAPPING = {
    "manufacturing": "manufacturing",
    "manufacture": "manufacturing",
    "services": "services",
    "service": "services",
    "trading": "trading",
    "trade": "trading",
    "retail": "trading",
    "agriculture": "agriculture_allied",
    "agri": "agriculture_allied",
    "farming": "agriculture_allied",
    "agriculture_allied": "agriculture_allied"
}

STATE_MAPPING = {
    "all_india": "all_india",
    "all india": "all_india",
    "pan india": "all_india",
    "maharashtra": "maharashtra",
    "karnataka": "karnataka",
    "tamil nadu": "tamil_nadu",
    "tamilnadu": "tamil_nadu",
    "delhi": "delhi",
    "gujarat": "gujarat"
}

def normalize_text(text: str) -> str:
    if not text:
        return ""
    return str(text).strip()

def normalize_slug(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s_]+', '-', s)
    return s.strip('-')

def normalize_id(text: str) -> str:
    s = text.upper().strip()
    s = re.sub(r'[^\w\s]', '', s)
    s = re.sub(r'[\s-]+', '_', s)
    return s

def normalize_tag(tag: str, mapping: Dict[str, str]) -> str:
    t_clean = tag.lower().strip().replace("_", " ")
    return mapping.get(t_clean, tag.lower().strip().replace(" ", "_"))

def normalize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively clean up values in the dictionary before loading into Pydantic."""
    if not isinstance(data, dict):
        return data

    cleaned = {}
    for k, v in data.items():
        if isinstance(v, dict):
            cleaned[k] = normalize_dict(v)
        elif isinstance(v, list):
            cleaned[k] = [normalize_dict(x) if isinstance(x, dict) else x for x in v]
        else:
            cleaned[k] = v

    # Root structural normalizations
    if "scheme" in cleaned and isinstance(cleaned["scheme"], dict):
        sch = cleaned["scheme"]
        # Enforce ID
        if "id" in sch:
            sch["id"] = normalize_id(sch["id"])
        # Enforce slug
        if "slug" in sch:
            sch["slug"] = normalize_slug(sch["slug"])
        elif "name" in sch:
            sch["slug"] = normalize_slug(sch["name"])
            
        # Provider normalization
        if "provider" in sch and isinstance(sch["provider"], dict):
            prov = sch["provider"]
            if "category" in prov:
                prov["category"] = prov["category"].lower().strip().replace(" ", "_")
            if "government_level" in prov:
                prov["government_level"] = prov["government_level"].lower().strip()

        # Geography normalization
        if "geography" in sch and isinstance(sch["geography"], dict):
            geo = sch["geography"]
            if "coverage" in geo:
                geo["coverage"] = geo["coverage"].lower().strip().replace(" ", "_")
            if "states" in geo and isinstance(geo["states"], list):
                geo["states"] = [normalize_tag(s, STATE_MAPPING) for s in geo["states"]]

        # Tags normalization
        if "tags" in sch and isinstance(sch["tags"], dict):
            t = sch["tags"]
            if "sectors" in t and isinstance(t["sectors"], list):
                t["sectors"] = [normalize_tag(sec, SECTOR_MAPPING) for sec in t["sectors"]]
            if "msme_segments" in t and isinstance(t["msme_segments"], list):
                t["msme_segments"] = [s.lower().strip() for s in t["msme_segments"]]

    # Normalize benefits
    if "benefits" in cleaned and isinstance(cleaned["benefits"], list):
        for ben in cleaned["benefits"]:
            if isinstance(ben, dict):
                if "id" in ben:
                    ben["id"] = normalize_id(ben["id"])
                if "category" in ben:
                    ben["category"] = ben["category"].lower().strip().replace(" ", "_")

    # Normalize eligibility rules
    if "eligibility_rules" in cleaned and isinstance(cleaned["eligibility_rules"], list):
        for rule in cleaned["eligibility_rules"]:
            if isinstance(rule, dict):
                if "id" in rule:
                    rule["id"] = normalize_id(rule["id"])
                if "parameter" in rule:
                    rule["parameter"] = rule["parameter"].lower().strip()
                if "operator" in rule:
                    rule["operator"] = rule["operator"].upper().strip()
                if "value" in rule and rule["parameter"] == "business.sector":
                    val = rule["value"]
                    if isinstance(val, str):
                        rule["value"] = normalize_tag(val, SECTOR_MAPPING)
                    elif isinstance(val, list):
                        rule["value"] = [normalize_tag(x, SECTOR_MAPPING) for x in val]

    return cleaned
