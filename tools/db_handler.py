import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "policies.db")

def init_db():
    """Initializes the database and creates the policies table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS policies (
            policy_id TEXT PRIMARY KEY,
            jurisdiction TEXT NOT NULL,
            policy_name TEXT NOT NULL,
            source_url TEXT NOT NULL,
            status TEXT NOT NULL,
            last_updated TEXT NOT NULL,
            summary_ai_generated TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def get_policy(policy_id):
    """Retrieves a policy by its ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT policy_id, jurisdiction, policy_name, source_url, status, last_updated, summary_ai_generated FROM policies WHERE policy_id = ?", (policy_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "policy_id": row[0],
            "jurisdiction": row[1],
            "policy_name": row[2],
            "source_url": row[3],
            "status": row[4],
            "last_updated": row[5],
            "summary_ai_generated": row[6]
        }
    return None

def upsert_policy(policy_data):
    """
    Upserts a policy record.
    Returns:
        tuple (status_changed, old_status, new_status)
    """
    init_db()
    policy_id = policy_data["policy_id"]
    jurisdiction = policy_data["jurisdiction"]
    policy_name = policy_data["policy_name"]
    source_url = policy_data["source_url"]
    status = policy_data["status"]
    last_updated = policy_data["last_updated"]
    summary_ai_generated = policy_data["summary_ai_generated"]

    existing = get_policy(policy_id)
    status_changed = False
    old_status = None

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if existing:
        if existing["status"] != status:
            status_changed = True
            old_status = existing["status"]
        
        cursor.execute("""
            UPDATE policies
            SET jurisdiction = ?,
                policy_name = ?,
                source_url = ?,
                status = ?,
                last_updated = ?,
                summary_ai_generated = ?
            WHERE policy_id = ?
        """, (jurisdiction, policy_name, source_url, status, last_updated, summary_ai_generated, policy_id))
    else:
        cursor.execute("""
            INSERT INTO policies (policy_id, jurisdiction, policy_name, source_url, status, last_updated, summary_ai_generated)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (policy_id, jurisdiction, policy_name, source_url, status, last_updated, summary_ai_generated))
        # Initial insertion can count as a transition from "None" or not trigger status change
    
    conn.commit()
    conn.close()

    return status_changed, old_status, status

def get_all_policies():
    """Retrieves all policies from the database."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT policy_id, jurisdiction, policy_name, source_url, status, last_updated, summary_ai_generated FROM policies ORDER BY last_updated DESC")
    rows = cursor.fetchall()
    conn.close()
    
    policies = []
    for row in rows:
        policies.append({
            "policy_id": row[0],
            "jurisdiction": row[1],
            "policy_name": row[2],
            "source_url": row[3],
            "status": row[4],
            "last_updated": row[5],
            "summary_ai_generated": row[6]
        }
    )
    return policies

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at:", DB_PATH)
