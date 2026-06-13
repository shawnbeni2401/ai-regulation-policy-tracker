import os
import sys
import hashlib

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from db_handler import upsert_policy
from normalize import validate_and_normalize

def populate_global_data():
    global_policies = [
        {
            "policy_id": hashlib.sha256(b"INDIA_MEITY_2025").hexdigest()[:16],
            "jurisdiction": "India",
            "policy_name": "India AI Governance Guidelines (Ministry of Electronics and Information Technology)",
            "source_url": "https://www.meity.gov.in/",
            "status": "Enforced",
            "last_updated": "2025-11-28T12:00:00Z",
            "summary_ai_generated": (
                "### AI Regulation Summary: India AI Governance Guidelines\n\n"
                "**Scope & Coverage:**\n"
                "- Intermediaries, generative platforms, and enterprise AI tools.\n"
                "- Focuses on bias prevention, electoral integrity, and deepfake mitigation.\n\n"
                "**Key Developer Obligations:**\n"
                "- Tagging or watermarking all AI-generated content to verify authenticity.\n"
                "- Conducting algorithmic bias assessments to prevent discrimination.\n"
                "- Filing transparency reports with MeitY for user-facing models.\n\n"
                "**Enforcement Timeline & Deadlines:**\n"
                "- Initial advisories active immediately; comprehensive compliance auditing active since late 2025.\n\n"
                "**Regulatory Oversight:**\n"
                "- Managed and enforced directly by MeitY and national cyber crime cells."
            )
        },
        {
            "policy_id": hashlib.sha256(b"CHINA_CAC_GENAI_2023").hexdigest()[:16],
            "jurisdiction": "China",
            "policy_name": "CAC Interim Measures for Generative Artificial Intelligence Services",
            "source_url": "https://www.cac.gov.cn/",
            "status": "Enforced",
            "last_updated": "2023-08-15T00:00:00Z",
            "summary_ai_generated": (
                "### AI Regulation Summary: CAC Generative AI Measures\n\n"
                "**Scope & Coverage:**\n"
                "- Public-facing generative AI platforms, chat services, and image synthesis systems.\n"
                "- Focuses on ideological alignment, intellectual property, and model security.\n\n"
                "**Key Developer Obligations:**\n"
                "- Undergoing CAC security assessments before launching public models.\n"
                "- Submitting algorithm details under the national algorithm filing system.\n"
                "- Verifying user identities and handling reports of illegal or biased model content within 24 hours.\n\n"
                "**Enforcement Timeline & Deadlines:**\n"
                "- Officially enforced starting August 15, 2023. Algorithm audits are ongoing.\n\n"
                "**Regulatory Oversight:**\n"
                "- Supervised by the Cyberspace Administration of China (CAC) in coordination with ministry partners."
            )
        },
        {
            "policy_id": hashlib.sha256(b"CANADA_AIDA_C27").hexdigest()[:16],
            "jurisdiction": "Canada",
            "policy_name": "Canada Artificial Intelligence and Data Act (AIDA - Bill C-27)",
            "source_url": "https://ised-isde.canada.ca/site/innovation-science-economic-development-canada/en",
            "status": "Proposed",
            "last_updated": "2024-04-18T12:00:00Z",
            "summary_ai_generated": (
                "### AI Regulation Summary: Canada AIDA (Bill C-27)\n\n"
                "**Scope & Coverage:**\n"
                "- High-impact AI applications deployed in commercial commerce.\n"
                "- Covers biased outputs, hiring applications, and biometric assessments.\n\n"
                "**Key Developer Obligations:**\n"
                "- Implementing risk mitigation policies to identify and prevent systemic bias.\n"
                "- Publishing public documentation outlining the system capabilities and data source metrics.\n"
                "- Establishing internal data governance rules to ensure privacy protection.\n\n"
                "**Enforcement Timeline & Deadlines:**\n"
                "- Under legislative review; targeted compliance rules projected to enter force by late 2026 if passed.\n\n"
                "**Regulatory Oversight:**\n"
                "- Administered by the newly proposed office of the Artificial Intelligence and Data Commissioner."
            )
        },
        {
            "policy_id": hashlib.sha256(b"OECD_AI_PRINCIPLES_2024").hexdigest()[:16],
            "jurisdiction": "Global",
            "policy_name": "OECD Recommendations on Artificial Intelligence (Updated 2024)",
            "source_url": "https://legalinstruments.oecd.org/en/instruments/OECD-LEGAL-0449",
            "status": "Passed",
            "last_updated": "2024-05-03T12:00:00Z",
            "summary_ai_generated": (
                "### AI Regulation Summary: OECD AI Principles\n\n"
                "**Scope & Coverage:**\n"
                "- Global intergovernmental guidance for trustworthy AI design and deployment.\n"
                "- Focuses on transparency, robust safety systems, and information integrity.\n\n"
                "**Key Developer Obligations:**\n"
                "- Designing models with explainable logic and query traceability.\n"
                "- Implementing proactive security metrics to prevent malicious exploits.\n"
                "- Ensuring models align with democratic values, human rights, and privacy norms.\n\n"
                "**Enforcement Timeline & Deadlines:**\n"
                "- Non-binding framework; adopted internationally in 2019 and revised in May 2024 to cover LLM guardrails.\n\n"
                "**Regulatory Oversight:**\n"
                "- Managed by the OECD Secretariat and tracked through the OECD AI Policy Observatory."
            )
        }
    ]

    print("Populating global policy records...")
    success_count = 0
    for policy in global_policies:
        cleaned, err = validate_and_normalize(policy)
        if cleaned:
            changed, _, _ = upsert_policy(cleaned)
            print(f"Successfully upserted: {cleaned['policy_name']} ({cleaned['jurisdiction']})")
            success_count += 1
        else:
            print(f"Validation failed for {policy['policy_name']}: {err}")
            
    print(f"Data population completed. Successfully added/updated {success_count} records.")

if __name__ == "__main__":
    populate_global_data()
