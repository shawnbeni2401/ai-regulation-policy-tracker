import os
import sys
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from db_handler import upsert_policy, get_policy

NOTIFICATIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".tmp", "notifications")

def trigger_alert(policy, old_status, new_status):
    """Generates and records a simulated webhook and email notification payload."""
    os.makedirs(NOTIFICATIONS_DIR, exist_ok=True)
    
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    alert_payload = {
        "event_id": f"evt_{int(datetime.utcnow().timestamp())}",
        "event_type": "policy.status_changed",
        "timestamp": timestamp,
        "data": {
            "policy_id": policy["policy_id"],
            "policy_name": policy["policy_name"],
            "jurisdiction": policy["jurisdiction"],
            "previous_status": old_status,
            "current_status": new_status,
            "source_url": policy["source_url"],
            "last_updated": policy["last_updated"]
        }
    }
    
    # 1. Simulate Webhook
    webhook_log = f"webhook_alert_{policy['policy_id']}_{int(datetime.utcnow().timestamp())}.json"
    webhook_path = os.path.join(NOTIFICATIONS_DIR, webhook_log)
    with open(webhook_path, 'w') as f:
        json.dump(alert_payload, f, indent=2)
        
    # 2. Simulate Email Alert Text
    email_log = f"email_alert_{policy['policy_id']}_{int(datetime.utcnow().timestamp())}.txt"
    email_path = os.path.join(NOTIFICATIONS_DIR, email_log)
    
    email_text = f"""
================================================================================
ALERT: AI POLICY STATUS UPDATED
================================================================================
Time: {timestamp}
Policy: {policy['policy_name']}
Jurisdiction: {policy['jurisdiction']}
Status Change: {old_status} ----> {new_status}
Source URL: {policy['source_url']}

Summary:
{policy['summary_ai_generated']}

--------------------------------------------------------------------------------
This is an automated policy alert from the AI Regulation Tracker System.
================================================================================
"""
    with open(email_path, 'w') as f:
        f.write(email_text)
        
    print(f"\n[ALERT] [NOTIFICATION TRIGGERED] Policy '{policy['policy_name']}' transitioned from {old_status} to {new_status}!")
    print(f"   -> Webhook JSON payload written to: {webhook_path}")
    print(f"   -> Email TXT body written to: {email_path}\n")
    
    return alert_payload

def update_status_manually(policy_id, new_status):
    """Helper function to manually transition a policy status and fire notifications if changed."""
    policy = get_policy(policy_id)
    if not policy:
        print(f"Error: Policy ID '{policy_id}' not found.")
        return False
        
    old_status = policy["status"]
    if old_status == new_status:
        print(f"No change: Policy '{policy['policy_name']}' is already in status '{new_status}'.")
        return False
        
    # Perform upsert with updated status
    policy["status"] = new_status
    policy["last_updated"] = datetime.utcnow().isoformat() + "Z"
    
    changed, _, _ = upsert_policy(policy)
    if changed:
        trigger_alert(policy, old_status, new_status)
        return True
    return False

if __name__ == "__main__":
    # If run with command-line arguments: python trigger_notification.py <policy_id> <new_status>
    if len(sys.argv) == 3:
        p_id = sys.argv[1]
        n_status = sys.argv[2]
        update_status_manually(p_id, n_status)
    else:
        print("Usage: python trigger_notification.py <policy_id> <new_status>")
        print("Example: python trigger_notification.py test_id Enforced")
