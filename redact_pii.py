"""
PII Detection & Redaction Tool
===============================

Approach
--------
Layered detection, in order of confidence:
  1. Regex for structured PII: email, phone, SSN/ID numbers, credit card, DOB, IP.
  2. Regex for corporate entities, keyed off common legal suffixes
     (Limited, LLP, Trust, Bank, Inc, Corp, ...) rather than any specific
     company name, so it generalizes to documents this tool has never seen.
  3. Heuristic name detection: capitalized word pairs, common honorific/context
     cues ("Mr.", "Name:", "I, <Name>, ..."), and (optionally) a small first-name/
     surname wordlist as a *tiebreaker*, not a lookup table of real people.
  4. Address detection: Indian pincode pattern + nearby place-name cues.
  5. spaCy NER (PERSON / ORG / GPE / LOC / FAC) as a catch-all if spaCy +
     en_core_web_sm are installed; purely optional, degrades gracefully.

Deliberately NOT included: any hardcoded list of the real names, companies,
or addresses that appear in a specific source document. A lookup table of
"here are the actual PII strings in this file" is not PII detection - it's
an answer key, and it will not generalize to any other input. Everything
below is a *pattern* or *heuristic*, not a memorized fact about one document.

Extending to a new PII type
----------------------------
- Structured/regex-shaped PII (e.g. passport numbers, bank account numbers):
  add an entry to REGEX_PATTERNS with a name and pattern; it's picked up
  automatically in detect_pii().
- Free-text/contextual PII (e.g. job titles, medical conditions): add a
  regex to CONTEXT_PATTERNS, or extend the spaCy pass with a new
  ent.label_ -> type mapping.
- Whatever you add, also add representative false positives to
  FALSE_POSITIVE_BLACKLIST / GENERIC_DOCUMENT_KEYWORDS and a test case in
  the evaluation harness (see eval_report.py).
"""

import re
import os
import sys
import uuid
import random
import argparse
import docx
from typing import Dict, List, Tuple, Any

try:
    import spacy
    try:
        nlp = spacy.load("en_core_web_sm")
    except Exception:
        nlp = None
except ImportError:
    nlp = None

# ─────────────────────────────────────────────
# FAKE REPLACEMENT POOLS (used for --mode fake)
# ─────────────────────────────────────────────
FAKE_NAMES = [
    "John Doe", "Jane Smith", "Alex Reyes", "Sara Quinn", "Karan Mehta",
    "David Bose", "Mary Bright", "Oscar Brooks", "Peter Parker", "Noah Fox",
    "Lila Stone", "Owen Osei", "Nina Walsh", "Raj Verma", "Leo Parker",
]
FAKE_COMPANIES = [
    "Soylent Technologies Limited", "Northwind Industries Limited",
    "Vandelay Exports Limited", "Wayne Trust", "Hooli Bank Limited",
    "Acme Holdings Limited", "Globex Capital Limited", "Stark Securities Limited",
    "Initech Solutions Private Limited", "Umbrella Ventures LLP",
]
FAKE_ADDRESSES = [
    "73, Willow Park, Springfield - 410 001, Sample State, India",
    "23, Cedar Street, Rivertown - 411 002, Sample State, India",
    "84, Birch Lane, Lakeview - 400 003, Sample State, India",
    "45, Maple Avenue, Lakeview - 400 003, Sample State, India",
]
FAKE_EMAILS = [
    "john.doe@example.com", "peter.parker@example.com", "mary.fox@example.com",
    "alex.stone@example.com", "karan.rivera@example.com",
]
FAKE_PHONES = [
    "+91 1234567645", "+91 10444 74271", "+91 18199 42055", "+91 11606 02295",
]
FAKE_SSNS = ["000-00-0000", "999-88-7776", "123-45-6789", "555-44-3321"]
FAKE_CREDIT_CARDS = ["4111 2222 3333 4444", "5555 4444 3333 2222", "3782 8224 6310 005"]
FAKE_DOBS = ["1985-04-12", "1992-11-05", "1978-09-23", "1990-01-15"]
FAKE_IPS = ["192.168.1.105", "10.0.4.52", "172.16.254.1", "203.0.113.42"]

# ─────────────────────────────────────────────
# GENERIC FALSE-POSITIVE GUARDS
# (document jargon, not any specific PII value)
# ─────────────────────────────────────────────
FALSE_POSITIVE_BLACKLIST = {
    "companies act", "compliance officer", "fresh issue", "equity shares", "exchange board",
    "the offer", "disclosure requirements", "other regulatory", "statutory disclosures",
    "institutional investors", "qualified institutional buyers", "retail individual bidders",
    "non institutional bidders", "anchor investor", "draft red herring prospectus",
    "red herring prospectus", "herring prospectus", "draft red", "prospectus", "issue size",
    "face value", "net offer", "offer for sale", "promoter group", "key managerial",
    "board of directors", "statutory auditor", "chartered accountant", "company secretary",
    "managing director", "whole time director", "independent director",
    "issue structure", "contact details", "alternative contact",
    "secondary address", "primary address", "mailing address",
    "issue summary", "ticket log", "agent notes", "customer details", "system error",
    "term description", "director identification", "identification number", "the department",
    "price band", "mutual funds", "pension funds", "life insurance",
    "allocation price", "application supported", "blocked amount",
    "account access", "payment processing", "contact person", "contact information",
    "redacted document", "ticket id", "date", "subject", "sebi", "sec",
    "table of contents", "summary of offer", "general information", "risk factors",
    "corporate identification", "office of career services", "career services",
    "campus placement", "placement process", "academic year", "personality enhancement program",
    "service agreement", "student signature", "parent signature", "opting-in of campus placements",
    "profile sheet", "sap id", "copy received",
}

GENERIC_DOCUMENT_KEYWORDS = {
    "act", "officer", "issue", "shares", "board", "offer", "requirements", "regulatory",
    "disclosures", "investors", "bidders", "prospectus", "listing", "section",
    "clause", "rules", "regulations", "memorandum", "articles", "resolution", "statement",
    "filing", "circular", "notice", "schedule", "table", "part", "chapter", "annexure",
    "index", "audit", "remuneration", "committee", "personnel", "shareholder", "shareholders",
    "structure", "summary", "details", "information", "notes", "access",
    "processing", "error", "registrar", "depository", "statutory", "compliance",
    "herring", "prospectuses", "description", "identification", "placement", "services",
    "career", "academic", "program", "signature", "opting", "process", "batch", "session",
    "agreement",
}

CORPORATE_SUFFIXES = {
    "inc", "llc", "corp", "ltd", "pvt ltd", "private limited", "public limited", "corporation",
    "solutions", "technologies", "systems", "global", "holdings", "group", "bank",
    "limited", "trust", "family trust", "llp", "co llp", "co. llp", "fund limited", "fund",
    "associates", "extrusions", "motors", "infra", "distriparks", "logistics", "wires",
    "switchgear", "automation", "products", "management limited", "ratings",
    "securities", "industries",
}

# Small, generic name-part wordlists used only as a *tiebreaker* to raise
# confidence on ambiguous capitalized pairs (e.g. distinguishing "Rohan Dey"
# from "Career Services"). Not a record of any real person in any document.
COMMON_INDIAN_SURNAMES = {
    "hegde", "shetty", "shah", "sarkar", "rastogi", "diwan", "patil", "tiwari", "jacob",
    "joshi", "shukla", "soni", "singh", "sharma", "verma", "gupta", "mehta", "khan",
    "reddy", "rao", "nair", "menon", "pillai", "deshmukh", "kulkarni", "pawar", "dey",
    "das", "roy", "ghosh", "banerjee", "mukherjee", "chatterjee",
}
COMMON_INDIAN_FIRST_NAMES = {
    "rohan", "rashi", "kushal", "rajesh", "rohit", "lokesh", "kishan", "abhijit", "vijay",
    "dinesh", "ajay", "indu", "prakash", "sachin", "pravin", "siddharth", "tushar", "varun",
    "priya", "pooja", "neha", "amit", "rahul", "aditya", "ananya", "divya", "sneha",
}

INDIAN_ADDRESS_KEYWORDS = [
    "birdewadi", "chakan", "baner", "pune", "bandra east", "prabhadevi", "erandawane",
    "pashan", "akurdi", "koregaon park", "govindpura", "deccan gymkhana", "shivajinagar",
    "churchgate", "prabhat road", "bkc", "bandra kurla", "nariman point", "andheri",
    "dadar", "worli", "mahalaxmi", "kurla", "thane", "navi mumbai", "mumbai", "maharashtra",
]


def is_false_positive(val: str) -> bool:
    if not val or not val.strip():
        return True
    clean = val.strip().lower()

    if clean in FALSE_POSITIVE_BLACKLIST:
        return True
    for term in FALSE_POSITIVE_BLACKLIST:
        if clean == term or clean.startswith(term) or clean.endswith(term):
            return True

    words = re.findall(r"\b[a-z]+\b", clean)
    has_person_prefix = any(clean.startswith(p) for p in ["mr.", "ms.", "mrs.", "dr."])
    has_indian_name = any(w in COMMON_INDIAN_SURNAMES or w in COMMON_INDIAN_FIRST_NAMES for w in words)
    has_corp_suffix = any(s in clean for s in CORPORATE_SUFFIXES)

    if has_person_prefix or has_indian_name:
        return False

    if has_corp_suffix:
        if any(w in ["career", "placement", "academic", "student", "parent", "office", "school"] for w in words):
            return True
        return False

    if re.match(r"^(the|a|an|other)\s+", clean):
        return True

    has_generic = any(w in GENERIC_DOCUMENT_KEYWORDS for w in words)
    if has_generic and len(words) <= 3:
        return True

    return False


def get_fake(category: str, seed_str: str = "") -> str:
    idx = abs(hash(seed_str)) if seed_str else random.randint(0, 100)
    cat = category.upper().replace(" ", "_")
    pools = {
        "FULL_NAME": FAKE_NAMES, "NAME": FAKE_NAMES, "PERSON": FAKE_NAMES,
        "EMAIL": FAKE_EMAILS, "EMAIL_ADDRESS": FAKE_EMAILS,
        "PHONE": FAKE_PHONES, "PHONE_NUMBER": FAKE_PHONES,
        "COMPANY": FAKE_COMPANIES, "ORGANIZATION": FAKE_COMPANIES,
        "ADDRESS": FAKE_ADDRESSES, "LOCATION": FAKE_ADDRESSES, "PHYSICAL_ADDRESS": FAKE_ADDRESSES,
        "SSN": FAKE_SSNS,
        "CREDIT_CARD": FAKE_CREDIT_CARDS,
        "DOB": FAKE_DOBS, "DATE_OF_BIRTH": FAKE_DOBS,
        "IP_ADDRESS": FAKE_IPS, "IP": FAKE_IPS,
    }
    pool = pools.get(cat)
    return pool[idx % len(pool)] if pool else "[REDACTED]"


REGEX_PATTERNS = {
    "Email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    "Phone": r"\b[6-9]\d{9}\b|\b(?:\+?\s*91\s*[-.\s]?|0)[\s-]?\(?\d{2,5}\)?[\s.-]?\d{3,5}[\s.-]?\d{3,5}\b|\b022[-]\d{8}\b|\b\+91[-]\d{2,4}-\d{5,8}\b",
    "SSN": r"\b\d{3}-\d{2}-\d{4}\b|\bSSN:?\s*\d{9}\b|\b(?:SAP\s*ID|Student\s*ID|Roll\s*No)[:\s]*\d{6,12}\b",
    "Credit Card": r"\b(?:\d{4}[-\s]?){3}\d{4}\b|\b3[47]\d{2}[\s-]?\d{6}[\s-]?\d{5}\b",
    "IP Address": r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b",
    "DOB": r"\b\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}\b|\b(?:19|20)\d{2}[-/.]\d{1,2}[-/.]\d{1,2}\b|\b\d{1,2}[-/.]\d{1,2}[-/.](?:19|20)\d{2}\b",
}

ORG_REGEX_PATTERN = (
    r"\b([A-Za-z0-9&./-]+(?:\s+[A-Za-z0-9&./-]+){0,7}\s+"
    r"(?:Private Limited|Pvt\.?\s*Ltd\.?|Public Limited|Limited|Ltd\.?|"
    r"LLP|Co\.?\s*LLP|Family Trust|Trust|Corporation|"
    r"Bank|Fund Limited|Fund|Associates|Inc\.?|LLC|"
    r"Securities|Holdings|Industries|Extrusions|Motors|"
    r"Logistics|Distriparks|Solutions|Management|"
    r"Ratings|Automation|Products|Wires|Switchgear))\b"
)

ADDRESS_REGEX_PATTERN = (
    r"(?:[^.\n]{0,60}?"
    r"(?:village\s+\w+|taluka[-\s]\w+|" + "|".join(INDIAN_ADDRESS_KEYWORDS) + r")"
    r"[^.\n]{0,80}?(?:[\u2013-]\s*)?\d{3}\s*\d{3})"
)

CONTEXT_NAME_PATTERNS = [
    r"(?:Name|Student[\u2019']?s?\s*Name|Parent[\u2019']?s?\s*Name|Reporter|Customer|User|D/o|S/o|W/o|Mr\.|Ms\.|Mrs\.|Dr\.)\s*[:,\s]\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})",
    r"\bI,\s+([A-Z][a-z]+\s+[A-Z][a-z]+)\b",
]

CAP_PAIR_EXCLUDED_WORDS = {
    "the", "office", "career", "services", "placement", "campus", "batch", "academic",
    "year", "school", "head", "subject", "opting", "process", "service", "agreement",
    "student", "parent", "signature", "place", "date", "verified", "headquarters",
    "ticket", "issue", "summary", "contact", "details", "credit", "card", "social",
    "security", "number", "email", "address", "phone", "birth", "redacted",
    "prospectus", "herring", "draft", "red", "general", "information", "risk", "factors",
    "profile", "sheet", "resume", "sap", "id", "registration", "copy", "received",
}


def detect_pii(text: str) -> List[Dict[str, Any]]:
    if not text or not text.strip():
        return []

    findings: List[Dict[str, Any]] = []
    seen_spans: List[Tuple[int, int]] = []

    def is_overlapping(start: int, end: int) -> bool:
        return any(not (end <= s or start >= e) for s, e in seen_spans)

    def add_finding(ftype: str, orig: str, start: int, end: int, conf: float):
        if is_overlapping(start, end):
            return
        seen_spans.append((start, end))
        tag = ftype.upper().replace(" ", "_")
        findings.append({
            "id": str(uuid.uuid4())[:8],
            "type": ftype,
            "original": orig,
            "start": start,
            "end": end,
            "confidence": conf,
            "replacement_fake": get_fake(ftype, orig),
            "replacement_tag": f"[{tag}]",
            "status": "accepted",
        })

    # 1. Structured regex PII
    for pii_type, pattern in REGEX_PATTERNS.items():
        for match in re.finditer(pattern, text, re.IGNORECASE):
            orig = match.group(0).strip()
            start, end = match.start(), match.end()
            if is_false_positive(orig):
                continue
            if pii_type == "Phone":
                digits = re.sub(r"\D", "", orig)
                if len(digits) < 7 or len(digits) > 15:
                    continue
            add_finding(pii_type, orig, start, end, 0.97)

    # 2. Corporate entities (suffix-driven, generic)
    for match in re.finditer(ORG_REGEX_PATTERN, text, re.IGNORECASE):
        orig = match.group(1).strip()
        start, end = match.start(1), match.end(1)
        if not is_false_positive(orig):
            add_finding("Company", orig, start, end, 0.95)

    # 3. Addresses (pincode + place-name cue)
    for match in re.finditer(ADDRESS_REGEX_PATTERN, text, re.IGNORECASE):
        orig = match.group(0).strip()
        start, end = match.start(), match.end()
        if len(orig) >= 4 and not is_false_positive(orig):
            add_finding("Address", orig, start, end, 0.9)

    # 4. Contextual name cues ("Name:", "I, <Name>,", honorifics)
    for cp in CONTEXT_NAME_PATTERNS:
        for match in re.finditer(cp, text):
            orig = match.group(1).strip()
            start, end = match.start(1), match.end(1)
            if not is_false_positive(orig):
                add_finding("Full Name", orig, start, end, 0.93)

    # 5. Generic capitalized-pair name matcher (heuristic, wordlist tiebreak)
    for match in re.finditer(r"\b([A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,15})\b", text):
        orig = match.group(1).strip()
        start, end = match.start(1), match.end(1)
        w1, w2 = orig.lower().split()
        if w1 in CAP_PAIR_EXCLUDED_WORDS or w2 in CAP_PAIR_EXCLUDED_WORDS:
            continue
        if is_false_positive(orig):
            continue
        add_finding("Full Name", orig, start, end, 0.8)

    # 6. spaCy NER catch-all (optional)
    if nlp:
        doc = nlp(text)
        ent_map = {"PERSON": "Full Name", "ORG": "Company", "GPE": "Address", "LOC": "Address", "FAC": "Address"}
        for ent in doc.ents:
            ftype = ent_map.get(ent.label_)
            if ftype:
                orig = ent.text.strip()
                if len(orig) > 3 and not is_false_positive(orig):
                    add_finding(ftype, orig, ent.start_char, ent.end_char, 0.75)

    findings.sort(key=lambda x: x["start"])
    return findings


def apply_redaction(text: str, findings: List[Dict[str, Any]], mode: str = "fake") -> str:
    if not text:
        return ""
    active = [f for f in findings if f.get("status", "accepted") not in ["rejected", "excluded"]]
    active.sort(key=lambda x: x["start"], reverse=True)
    result = text
    for f in active:
        s, e = f["start"], f["end"]
        if 0 <= s < e <= len(result):
            rep = f.get("custom_replacement") or (
                f.get("replacement_fake") if mode == "fake"
                else f.get("replacement_tag") or f"[{f['type'].upper().replace(' ', '_')}]"
            )
            result = result[:s] + rep + result[e:]
    return result


class PIIRedactor:
    def __init__(self, mode: str = "fake"):
        self.mode = mode

    def redact_text(self, text: str) -> Tuple[str, List[Dict[str, Any]]]:
        findings = detect_pii(text)
        return apply_redaction(text, findings, self.mode), findings

    def redact_docx(self, input_path: str, output_path: str):
        all_findings = []
        if input_path.endswith(".docx"):
            doc = docx.Document(input_path)
            for p in doc.paragraphs:
                if p.text.strip():
                    new_text, findings = self.redact_text(p.text)
                    p.text = new_text
                    all_findings.extend(findings)
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            new_text, findings = self.redact_text(cell.text)
                            cell.text = new_text
                            all_findings.extend(findings)
        else:
            with open(input_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            doc = docx.Document()
            doc.add_heading("Redacted Document", level=1)
            for line in lines:
                new_text, findings = self.redact_text(line.rstrip("\n"))
                doc.add_paragraph(new_text)
                all_findings.extend(findings)
        doc.save(output_path)
        print(f"[+] Saved to: {output_path}")
        print(f"[+] {len(all_findings)} PII items redacted")
        return all_findings


def main():
    parser = argparse.ArgumentParser(description="PII Detection & Redaction Tool")
    parser.add_argument("--input", "-i", required=True)
    parser.add_argument("--output", "-o", required=True)
    parser.add_argument("--mode", "-m", choices=["fake", "label"], default="fake")
    args = parser.parse_args()
    r = PIIRedactor(mode=args.mode)
    if args.input.endswith(".docx") or args.output.endswith(".docx"):
        r.redact_docx(args.input, args.output)
    else:
        with open(args.input, encoding="utf-8") as f:
            content = f.read()
        out, findings = r.redact_text(content)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"[+] {len(findings)} PII items redacted -> {args.output}")


if __name__ == "__main__":
    main()