import os
import json
import re
from datetime import datetime

# Load schema if available, else use a hardcoded equivalent for resilience
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".tmp", "schema.json")
QUARANTINE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".tmp", "quarantine")

def load_schema():
    if os.path.exists(SCHEMA_PATH):
        try:
            with open(SCHEMA_PATH, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return None

def validate_and_normalize(raw_data):
    """
    Validates the raw data dictionary against the schema.
    Returns:
        tuple: (validated_data_dict, error_message)
        If valid, error_message is None. If invalid, validated_data_dict is None.
    """
    errors = []
    
    # 1. Field Extraction & Fallbacks
    policy_id = raw_data.get("policy_id")
    jurisdiction = raw_data.get("jurisdiction")
    policy_name = raw_data.get("policy_name")
    source_url = raw_data.get("source_url")
    status = raw_data.get("status")
    last_updated = raw_data.get("last_updated")
    summary_ai_generated = raw_data.get("summary_ai_generated", "")

    # 2. Basic Required Fields Check
    required = ["policy_id", "jurisdiction", "policy_name", "source_url", "status", "last_updated", "summary_ai_generated"]
    for field in required:
        if raw_data.get(field) is None or str(raw_data.get(field)).strip() == "":
            errors.append(f"Missing required field: '{field}'")

    if errors:
        quarantine_record(raw_data, errors)
        return None, "; ".join(errors)

    # 3. Normalize Jurisdiction
    jurisdiction_raw = str(jurisdiction).upper().strip()
    if jurisdiction_raw in ["US", "USA", "UNITED STATES", "UNITED STATES OF AMERICA"]:
        jurisdiction = "US"
    elif jurisdiction_raw in ["EU", "EUROPE", "EUROPEAN UNION"]:
        jurisdiction = "EU"
    elif jurisdiction_raw in ["UK", "UNITED KINGDOM", "DSIT"]:
        jurisdiction = "UK"
    elif jurisdiction_raw in ["GLOBAL", "INTERNATIONAL", "OECD"]:
        jurisdiction = "Global"
    elif jurisdiction_raw in ["INDIA", "IN", "MEITY"]:
        jurisdiction = "India"
    elif jurisdiction_raw in ["CHINA", "CN", "CAC"]:
        jurisdiction = "China"
    elif jurisdiction_raw in ["CANADA", "CA", "AIDA"]:
        jurisdiction = "Canada"
    else:
        jurisdiction = jurisdiction_raw.title()

    
    # 4. Normalize Status
    status = str(status).strip().title()
    allowed_statuses = ["Proposed", "Under Review", "Passed", "Enforced"]
    # Mapping helper
    status_map = {
        "Draft": "Proposed",
        "Active": "Enforced",
        "Enacted": "Passed",
        "Proposed": "Proposed",
        "Under Review": "Under Review",
        "Passed": "Passed",
        "Enforced": "Enforced"
    }
    if status in status_map:
        status = status_map[status]
    else:
        errors.append(f"Invalid status '{status}'. Must be one of: {allowed_statuses}")

    # 5. Normalize last_updated to ISO 8601
    normalized_date = None
    date_str = str(last_updated).strip()
    # Attempt common date formats
    date_formats = [
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%B %d, %Y",
        "%d %B %Y",
        "%Y/%m/%d"
    ]
    for fmt in date_formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            normalized_date = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            break
        except ValueError:
            continue
    
    if not normalized_date:
        # Check if it matches ISO 8601 manually via regex or fallback to current time
        if re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$', date_str):
            normalized_date = date_str
        else:
            errors.append(f"Invalid last_updated format '{date_str}'. Could not parse to ISO 8601.")
    
    # 6. Validate source_url matches URI format
    url_pattern = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' # domain...
        r'localhost|' # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    if not url_pattern.match(str(source_url)):
        errors.append(f"Invalid source_url format: '{source_url}'")

    if errors:
        quarantine_record(raw_data, errors)
        return None, "; ".join(errors)

    # 7. Package Cleaned Data
    cleaned_data = {
        "policy_id": str(policy_id).strip(),
        "jurisdiction": jurisdiction,
        "policy_name": str(policy_name).strip(),
        "source_url": str(source_url).strip(),
        "status": status,
        "last_updated": normalized_date,
        "summary_ai_generated": str(summary_ai_generated).strip()
    }
    return cleaned_data, None

def quarantine_record(raw_data, errors):
    """Saves the invalid raw record along with its validation errors to the quarantine path."""
    os.makedirs(QUARANTINE_DIR, exist_ok=True)
    filename = f"failed_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hash(str(raw_data)) % 100000}.json"
    filepath = os.path.join(QUARANTINE_DIR, filename)
    payload = {
        "raw_record": raw_data,
        "quarantine_timestamp": datetime.utcnow().isoformat() + "Z",
        "errors": errors
    }
    with open(filepath, 'w') as f:
        json.dump(payload, f, indent=2)
    print(f"[QUARANTINE] Record failed validation and was saved to {filepath}. Errors: {errors}")

if __name__ == "__main__":
    # Self-test code
    test_ok = {
        "policy_id": "test_hash_01",
        "jurisdiction": "US Gov",
        "policy_name": "Executive Order on Trustworthy AI",
        "source_url": "https://www.whitehouse.gov/briefing-room",
        "status": "Draft",
        "last_updated": "2026-06-02",
        "summary_ai_generated": "AI summary goes here."
    }
    
    cleaned, err = validate_and_normalize(test_ok)
    if err:
        print("Self-test failed:", err)
    else:
        print("Self-test succeeded! Cleaned record:")
        print(json.dumps(cleaned, indent=2))
