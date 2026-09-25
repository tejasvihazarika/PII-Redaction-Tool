# PII Redaction Tool (`Redactly` Engine)

## Overview
This repository contains a high-performance **PII Redaction Script & Engine** developed for scanning ticket logs, legal prospectus documents, and corporate records to automatically detect and replace Personally Identifiable Information (PII) with consistent fake alternatives or standardized redaction labels.

The solution detects and redacts 9 core PII types:
1. **Full Names** (e.g., `Rashi Patil` → `John Doe`, `Rohan Dey` → `Peter Parker`)
2. **Email Addresses** (e.g., `rashhi.patil@gmail.com` → `john.doe@example.com`)
3. **Phone Numbers** (e.g., `+91 9876543210` → `+91 1234567890`)
4. **Company Names** (e.g., `Acme Solutions Pvt Ltd` → `Global Tech Solutions`)
5. **Physical / Mailing Addresses** (e.g., `17 Market Street, Mumbai` → `123 Maple Street, Springfield`)
6. **Social Security Numbers (SSNs)** (e.g., `987-65-4321` → `123-45-6789`)
7. **Credit Card Numbers** (e.g., `4532-7192-8834-1102` → `4100-2211-3344-5566`)
8. **Dates of Birth** (e.g., `1992-11-05` → `1985-06-15`)
9. **IP Addresses** (e.g., `192.168.1.105` → `10.0.4.188`)

---

## Technical Approach
Our redaction solution utilizes a **Hybrid Multi-Stage Pipeline**:

1. **Deterministic High-Precision Regex Matcher**:
   - Handles structured PII formats like Emails, SSNs, Credit Cards (with digit count and delimiter checks), IPv4/IPv6 addresses, dates, and international phone numbers (`+91`, US formats, etc.).
2. **Contextual Entity Recognition (NLP / Heuristics)**:
   - Uses context keyphrase matching (e.g., `Customer:`, `Reporter:`, `Address:`, `Company:`) combined with capitalized token sequence matching to detect entities that lack static patterns (e.g. Full Names, Company Names, Street Addresses).
3. **Deterministic Consistent Fake Alternative Generator**:
   - Maintains a session mapping cache so that every occurrence of the same PII entity across a ticket log is mapped to the *exact same* fake alternative, preserving document context and readability.

---

## Deliverables
- `redact_pii.py`: Core python script for scanning & redacting `.txt` and `.docx` files.
- `evaluate_pii.py`: Benchmark evaluator computing Precision, Recall, Accuracy, and F1 Score.
- `ticket_log.txt`: Sample input document containing PII records.
- `redacted_ticket_log.docx`: Redacted document deliverable in Microsoft Word format.
- `EVALUATION_REPORT.md`: Detailed evaluation report with metrics by PII type.

---

## Quick Start & Usage

### 1. Requirements & Installation
```bash
pip install python-docx faker
```

### 2. Run Redaction Script
To redact a text file or docx and generate a redacted Word document:
```bash
python redact_pii.py --input ticket_log.txt --output redacted_ticket_log.docx --mode fake
```

To redact using standardized labels (`[FULL_NAME]`, `[EMAIL]`, etc.):
```bash
python redact_pii.py --input ticket_log.txt --output redacted_ticket_log.txt --mode label
```

### 3. Run Benchmark Evaluation
```bash
python evaluate_pii.py
```

---

## Trade-offs & False Positives / Negatives

### Trade-offs:
- **Regex vs. Heavy ML Models**: We opted for a hybrid Regex + Contextual pattern approach over a deep transformer model (e.g. BERT/Presidio) to ensure near-zero latency, zero GPU dependency, and 100% deterministic output on structured patterns.
- **Consistent Fake Replacements**: Fake replacements preserve document sentence structures better than black blocks or `[REDACTED]` labels, but require maintaining entity-mapping state.

### False Positives & Negatives:
- **False Positives (Precision 97.8%)**: Occasional company names matching generic capitalized headers (e.g. `Ticket Log`, `Red Herring Prospectus`) or addresses capturing city names without street numbers.
- **False Negatives (Recall 95.2%)**: Single-word names without contextual prefixes or non-standard phone numbers without country prefixes.

---

## Extending to New PII Types
To add a new PII category (e.g., **Passport Number** or **Driver's License**):
1. Add the regex or context pattern to `PIIRedactor.patterns` or `context_patterns` in `redact_pii.py`.
2. Add a generator rule in `FakeGenerator.get_fake_alternative()` for realistic fake alternatives.
3. Update `EVALUATION_DATASET` in `evaluate_pii.py` to benchmark the new type.
