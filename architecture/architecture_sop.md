# Layer 1: Architecture - Standard Operating Procedure (SOP)
## AI Regulation & Policy Tracker System

This SOP establishes the guidelines, resilience measures, and data verification guards for the ingestion, normalization, and persistence of AI policies.

---

### 1. Ingestion & Scraper Resilience
To prevent scrapers from being blocked and to handle temporary network failures, the scraping engine must implement the following controls:

* **Exponential Backoff with Jitter:**
  - Initial wait time: 2 seconds.
  - Backoff multiplier: 2x.
  - Maximum retries: 3.
  - Apply random jitter (+/- 0.5s) to avoid deterministic request patterns.
* **User-Agent Rotation:**
  - Rotate headers using a predefined list of modern web browser user-agents.
* **Timeout Budgets:**
  - Every HTTP/HTTPS request must have a strict connection timeout of 10 seconds and read timeout of 20 seconds.
* **Error Classification:**
  - Retry on HTTP 500, 502, 503, 504 and Network/Connection timeouts.
  - Fail immediately on HTTP 400, 401, 403, 404 (indicating authorization errors or broken links).

---

### 2. Data Cleaning & Normalization
Scraped HTML pages and documents can be highly unstructured. The normalization tool must clean raw text as follows:
* **HTML Stripping:** Use libraries like `BeautifulSoup` to strip HTML tags, CSS blocks, and scripts.
* **Whitespace Normalization:** Collapse multiple spaces, tabs, and newlines into single spaces or single newlines.
* **Metadata Extraction:** 
  - Standardize Dates to ISO 8601 format (`YYYY-MM-DDTHH:MM:SSZ`).
  - Standardize Jurisdictions (e.g., map "United States", "US Gov", "USA" to `"US"`; "EU", "European Union" to `"EU"`; etc.).
  - Map status labels to the strict enum: `["Proposed", "Under Review", "Passed", "Enforced"]`.

---

### 3. Schema Protection (The Ingestion Gate)
Before any record is upserted into the database, it must pass a validation check against the schema defined in `.tmp/schema.json`.
* **Required Fields Check:** Ensure all required keys (`policy_id`, `jurisdiction`, `policy_name`, `source_url`, `status`, `last_updated`, `summary_ai_generated`) are present.
* **Type Validation:** Check that `policy_id` is a hash/string, `source_url` is a valid URL string, etc.
* **Enum Validation:** Ensure `status` matches one of the allowed enum values.
* **Quarantine Flow:** If validation fails, write the record to a quarantine path (`.tmp/quarantine/`) with a timestamp and error details, and log the failure. Do not push invalid records to the production database.

---

### 4. LLM Summary Protocol (Layer 2)
Dense documents or PDF files are parsed, and their text is passed to Gemini 3.5 Flash inside Antigravity (or simulated using a helper function in our toolchain) to create a concise, markdown-compliant summary.
* **Prompt Template:**
  ```text
  You are an expert AI policy analyst. Summarize the following dense government regulatory document.
  Focus on:
  1. Scope (e.g., target technologies like LLMs, computer vision, data privacy).
  2. Key obligations and compliance deadlines for developers.
  3. Enforcement penalties and regulatory bodies involved.
  Keep the summary under 300 words. Format with clean markdown headers and bullet points.
  ```
* **Text Chunking:** If the document text exceeds token limits, extract only the Executive Summary, Preamble, and Table of Contents to feed into the summarizer.
