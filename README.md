# PII Redaction Tool (`Redactly` Engine)

## Overview
This repository contains a production-grade **PII Redaction Engine & Interactive Web Application** developed for scanning ticket logs, legal red herring prospectuses, placement forms, and corporate documents to automatically detect and replace Personally Identifiable Information (PII) with consistent fake alternatives or standardized redaction labels.

Live Demo: **[https://tejasvihazarika.github.io/PII-Redaction-Tool/](https://tejasvihazarika.github.io/PII-Redaction-Tool/)**

The solution detects and redacts 10 core PII types:
1. **Full Names** (e.g., `Rashi Patil` → `John Doe`, `Tejasvi Hazarika` → `Alex Morgan`)
2. **Email Addresses** (e.g., `rashhi.patil@gmail.com` → `john.doe@example.com`)
3. **Phone Numbers** (e.g., `+91 9876543210` / `9999069169` → `+91 1234567890`)
4. **Company / Institutional Names** (e.g., `Acme Solutions Pvt Ltd` → `Global Tech Solutions`)
5. **Physical / Mailing Addresses** (e.g., `17 Market Street, Mumbai` → `123 Maple Street, Springfield`)
6. **Social Security Numbers / SAP IDs** (e.g., `500119060` → `987654321`)
7. **Credit Card Numbers** (e.g., `4532-7192-8834-1102` → `4100-2211-3344-5566`)
8. **Dates of Birth & Form Dates** (e.g., `28 April 2026` → `15 June 1985`)
9. **IP Addresses** (e.g., `192.168.1.105` → `10.0.4.188`)

---

## Technical Approach
Our redaction solution utilizes a **Hybrid Multi-Stage Pipeline**:

1. **Deterministic High-Precision Regex Matcher**:
   - Handles structured PII formats like Emails, 10-digit Indian Mobile Numbers, SSNs, Credit Cards, IPv4 addresses, text dates (`28 April 2026`), and international phone numbers.
2. **Contextual Entity Recognition & Window Heuristics**:
   - Uses context keyphrase matching (`I, <Name>`, `Name: <Name>`, `Parent's Name: <Name>`, `D/o <Name>`) combined with capitalized token sequence matching to detect entities lacking static patterns.
3. **Institutional Blacklist Filtering**:
   - Eliminates false positives on academic and legal document headers (e.g. *"The Office of Career Services"*, *"Campus Placement"*, *"Profile Sheet"*, *"Placement Process"*).
4. **Deterministic Consistent Fake Alternative Generator**:
   - Maintains a session hash map cache so that every occurrence of the same PII entity across a document is mapped to the *exact same* fake alternative, preserving document context and readability.

---

## Deliverables
- `redact_pii.py`: Core Python script for scanning & redacting `.txt` and `.docx` files.
- `server.py`: FastAPI server for document processing endpoints.
- `src/services/piiScanner.js`: Client-side JavaScript detection engine for zero-latency browser scanning.
- `redacted_ticket_log.docx`: Redacted document deliverable in Microsoft Word format.
- `Evaluation_Strategy_and_Metrics.docx`: Downloadable Word report detailing benchmark metrics, precision/recall, and evaluation methodology.
- `EVALUATION_REPORT.md`: Markdown evaluation report with detailed entity metrics.

---

## Quick Start & Usage

### 1. Requirements & Installation
```bash
pip install python-docx faker spacy fastapi uvicorn
python -m spacy download en_core_web_sm
```

### 2. Run Redaction Script
To redact a text file or docx and generate a redacted Word document:
```bash
python redact_pii.py --input ticket_log.txt --output redacted_ticket_log.docx --mode fake
```

### 3. Run Benchmark Evaluation
```bash
python evaluate_pii.py
```

---

## Cloud Hosting Architecture

- **Frontend Hosting**: **GitHub Pages** (Static React/Vite SPA hosted at `https://tejasvihazarika.github.io/PII-Redaction-Tool/`).
- **Backend Cloud Hosting Compatibility**:
  - **Render / Railway / Vercel**: The `server.py` FastAPI app is containerized/WSGI-configured and ready to be deployed to Render or Railway via Docker / Uvicorn.

---

## Trade-offs & Evaluation Summary

### Evaluation Metrics:
- **Macro Precision**: **98.1%** (Eliminated false positives on institutional form headers and document labels).
- **Macro Recall**: **98.1%** (High recall across Indian names, emails, 10-digit phone numbers, and dates).
- **Macro F1-Score**: **98.1%**
- **System Accuracy**: **98.5%**

### Trade-offs:
- **Regex + Rules vs. Large Language Models**: We opted for a hybrid Regex + Contextual pattern approach over heavy LLM calls to ensure near-zero latency, zero API cost/dependency, and 100% deterministic output on structured patterns.
- **Consistent Fake Replacements**: Fake replacements preserve document sentence structures better than black blocks or `[REDACTED]` labels.

---

## Extending to New PII Types
To add a new PII category (e.g., **Passport Number** or **Driver's License**):
1. Add the regex or context pattern to `regexes` in `src/services/piiScanner.js` and `redact_pii.py`.
2. Add a generator rule in `get_fake_alternative()` for realistic fake replacements.
3. Update `isFalsePositive` validator if specific keywords should be excluded.
