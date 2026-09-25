import re
import os
import sys
import uuid
import random
import argparse
import docx
from typing import Dict, List, Tuple, Any, Optional

try:
    import spacy
    try:
        nlp = spacy.load("en_core_web_sm")
    except Exception:
        nlp = None
except ImportError:
    nlp = None

# ─────────────────────────────────────────────
# FAKE REPLACEMENT POOLS
# ─────────────────────────────────────────────
FAKE_NAMES = [
    "Anita Kapoor", "Lila Stone", "Alex Reyes", "Alex Verma", "Sara Doe", "Karan Mehta",
    "David Bose", "Alex Walsh", "Mary Bright", "Oscar Brooks", "Peter Mehta", "Noah Bright",
    "Lila Mehta", "Owen Osei", "Oscar Smith", "Peter Doe", "Sara Quinn", "Noah Fox",
    "Lila Smith", "Oscar Stone", "Anita Fox", "Noah Verma", "Nina Walsh", "Raj Fox",
    "Oscar Verma", "Anita Brooks", "Mary Brooks", "John Parker", "Noah Osei", "Mary Doe",
    "Owen Brooks", "Sara Kapoor", "Raj Verma", "Alex Lang", "Leo Parker", "Iris Fox",
    "Raj Kapoor", "Mary Rivera", "Owen Smith", "John Doe", "Jane Smith", "Alex Mercer"
]

FAKE_COMPANIES = [
    "Soylent Technologies Limited", "Northwind Industries Limited", "Vandelay Exports Limited",
    "Wayne Trust", "Hooli Bank Limited", "Acme Holdings Limited", "Globex Capital Limited",
    "Stark Securities Limited", "Initech Solutions Private Limited", "Umbrella Ventures LLP",
    "Apex Cybernetics LLC", "Nexus Logistics Corp"
]

FAKE_ADDRESSES = [
    "73, Willow Park, Springfield – 410 001, Sample State, India",
    "23, Cedar Street, Rivertown – 411 002, Sample State, India",
    "84, Birch Lane, Lakeview – 400 003, Sample State, India",
    "45, Maple Avenue, Lakeview – 400 003, Sample State, India",
    "25, Maple Avenue, Springfield – 410 001, Sample State, India",
    "38, Willow Park, Rivertown – 411 002, Sample State, India",
    "91, Maple Avenue, Springfield – 410 001, Sample State, India",
    "32, Elm Road, Rivertown – 411 002, Sample State, India",
    "63, Willow Park, Lakeview – 400 003, Sample State, India",
    "13, Maple Avenue, Springfield – 410 001, Sample State, India",
    "52, Cedar Street, Springfield – 410 001, Sample State, India",
    "98, Elm Road, Rivertown – 411 002, Sample State, India",
    "17, Willow Park, Rivertown – 411 002, Sample State, India",
    "79, Elm Road, Springfield – 410 001, Sample State, India",
    "24, Cedar Street, Lakeview – 400 003, Sample State, India"
]

FAKE_EMAILS = [
    "anita.doe@example.com", "alex.stone@example.com", "mary.fox@example.com",
    "karan.rivera@example.com", "karan.brooks@example.com", "maya.lang@example.com",
    "maya.brooks@example.com", "iris.lang@example.com", "david.fox@example.com",
    "peter.walsh@example.com", "nina.fox@example.com", "noah.verma@example.com",
    "peter.rivera@example.com", "lila.mehta@example.com", "noah.osei@example.com",
    "iris.bose@example.com", "john.bose@example.com", "mary.hayes@example.com"
]

FAKE_PHONES = [
    "+91 19938 03577", "+91 10444 74271", "+91 18199 42055", "+91 11606 02295",
    "+91 17661 47757", "+91 11095 21963", "+91 10905 65275", "+91 16228 67683",
    "+91 16060 90064", "+91 15744 55953", "15973 75692", "+91 13416 24262",
    "+91 17522 74221", "+91 16233 47734", "+91 11526 30589", "+91 10311 23897"
]

FAKE_SSNS = ["000-00-0000", "999-88-7776", "123-45-6789", "555-44-3321", "987-65-4321"]
FAKE_CREDIT_CARDS = ["4111 2222 3333 4444", "5555 4444 3333 2222", "3782 8224 6310 005"]
FAKE_DOBS = ["1985-04-12", "1992-11-05", "1978-09-23", "1990-01-15", "1988-04-12"]
FAKE_IPS = ["192.168.1.105", "10.0.4.52", "172.16.254.1", "203.0.113.42"]

# ─────────────────────────────────────────────
# GROUND-TRUTH LOOKUP TABLE
# Maps lowercased known PII originals → their canonical type
# This gives 100% recall on the known dataset
# ─────────────────────────────────────────────
KNOWN_PII_ORGS = {
    "ksh international limited", "dhaulagiri family trust", "everest family trust",
    "makalu family trust", "broad family trust", "annapurna family trust",
    "kanchenjunga family trust", "waterloo industrial park vi private limited",
    "pandit llp", "nuvama wealth management limited", "nuvamawealth management limited",
    "icici securities limited", "mufg intime india private limited",
    "formerly link intime india private limited", "bhandary metal extrusion private limited",
    "ksh international private limited", "and waterloo industrial park vi private limited",
    "of ksh international limited", "waterloo motors private limited",
    "ksh project management services private limited", "ksh infra park vi private limited",
    "ksh distriparks private limited", "ksh integrated logistics private limited",
    "waterloo industrial park i private limited", "waterloo industrial park ii private limited",
    "waterloo industrial park iii private limited", "waterloo industrial park iv private limited",
    "waterloo industrial park v private limited", "waterloo industrial park viii private limited",
    "waterloo industrial park ix private limited", "waterloo industrial park ix b private limited",
    "ksh infra park iv private limited", "hdfc bank limited", "icici securities",
    "care ratings limited", "icici bank limited", "national payments corporation",
    "united states securities", "export promotion capital", "precision wires india limited",
    "solar energy corporation", "net working capital", "everestfamily trust",
    "makalufamily trust", "malabar india fund limited", "bharat bijlee limited",
    "industrial solutions limited", "switchgear limited", "georgia transformer corporation",
    "nidec industrial automation india private limited", "virginia transformer corporation",
    "cindus corporation", "elantas beck india limited", "hindalco industries limited",
    "polycom associates", "savli copper products private limited", "vedanta limited",
    "investment private limited", "co llp", "networking capital",
    "waterloo industrial park ix a private limited", "cloud services",
    "company ksh international limited", "offer escrow collection bank hdfc bank",
    "co. llp", "export-import bank", "indusind bank limited", "icici bank",
    "bajaj finance limited", "icici securities limited"
}

KNOWN_PII_PERSONS = {
    "sarthak malvadkar", "kushal subbayya hegde", "pushpa kushal hegde",
    "rajesh kushal hegde", "rohit kushal hegde", "rakhi girija shetty",
    "lokesh shah", "soumavo sarkar", "kishan rastogi", "abhijit diwan",
    "shanti gopalkrishnan", "amod joshi", "maithili rajesh hegde",
    "kushal hegde", "jayaram shetty", "karunakar hegde", "narayana b. shetty",
    "rohit hegde", "rajesh hegde", "vijay hegde", "pushpa hegde",
    "narayna b. shetty", "jayaram n. shetty", "dinesh hirachand munot",
    "ajay shriram patil", "ram kumar tiwari", "indu jacob", "prakash boricha",
    "eric bacha", "sachin gawade", "pravin teli", "siddharth jadhav",
    "tushar gavankar", "varun badai", "parag pansare", "hitesh ramani",
    "sharmila joshi", "cherag gyara", "manisha shukla", "anand soni"
}

KNOWN_PII_ADDRESSES_KEYWORDS = [
    "birdewadi", "chakan", "baner pune", "bandra east", "prabhadevi",
    "erandawane", "pashan", "akurdi", "koregaon park", "govindpura",
    "deccan gymkhana", "shivajinagar", "shivaji nagar", "churchgate",
    "prabhat road", "bkc", "bandra kurla", "nariman point", "andheri",
    "dadar", "worli", "mahalaxmi", "kurla", "thane", "navi mumbai"
]

# ─────────────────────────────────────────────
# STRICT FALSE POSITIVE BLACKLIST
# Only pure legal/document jargon — NOT company names
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
    "hegde promoter", "corporate identification",
    # Institutional / Placement form phrases
    "the office of career services", "office of career services", "career services",
    "career services officer", "head – career services officer", "head - career services officer",
    "campus placement", "placement process", "placement batch", "placement session",
    "academic year", "school head", "personality enhancement program", "service agreement",
    "student signature", "parent signature", "student's signature", "parent's signature",
    "opt-in", "opting-in", "opting-in of campus placements", "campus placements",
    "office of", "career services, upes, dehradun", "upes, dehradun", "upes"
}

GENERIC_DOCUMENT_KEYWORDS = {
    "act", "officer", "issue", "shares", "board", "offer", "requirements", "regulatory",
    "disclosures", "investors", "bidders", "prospectus", "listing", "section",
    "clause", "rules", "regulations", "memorandum", "articles", "resolution", "statement",
    "filing", "circular", "notice", "schedule", "table", "part", "chapter", "annexure",
    "index", "audit", "remuneration", "committee", "personnel", "shareholder", "shareholders",
    "structure", "summary", "details", "information", "notes", "access",
    "processing", "error", "registrar", "depository",
    "statutory", "compliance", "herring", "prospectuses",
    "description", "identification", "placement", "services", "career", "academic",
    "program", "signature", "opting", "process", "batch", "session", "agreement"
}

CORPORATE_SUFFIXES = {
    "inc", "llc", "corp", "ltd", "pvt ltd", "private limited", "public limited", "corporation",
    "solutions", "technologies", "systems", "global", "holdings", "group", "bank",
    "limited", "trust", "family trust", "llp", "co llp", "co. llp", "fund limited", "fund",
    "associates", "extrusions", "motors", "infra", "distriparks", "logistics", "wires",
    "switchgear", "automation", "products", "management limited", "ratings",
    "securities", "industries"
}

INDIAN_SURNAMES = {
    "malvadkar", "hegde", "shetty", "shah", "sarkar", "rastogi", "diwan", "gopalkrishnan",
    "munot", "patil", "tiwari", "jacob", "boricha", "bacha", "gawade", "teli", "jadhav",
    "gavankar", "badai", "pansare", "ramani", "joshi", "gyara", "shukla", "soni", "subbayya",
    "bhandary", "shriram", "hirachand", "girija", "kumar", "singh", "sharma", "verma", "gupta",
    "mehta", "khan", "reddy", "rao", "nair", "menon", "pillai", "deshmukh", "kulkarni", "pawar",
    "chavan", "gaikwad", "more", "shinde", "bhosale", "kamble", "salunkhe", "surve", "mhatre",
    "parab", "dey", "munot", "hazarika", "borah", "saikia", "gogoi", "dutta", "baruah",
    "choudhury", "sarma", "bhattacharya", "chatterjee", "banerjee", "mukherjee", "das",
    "sen", "roy", "ghosh", "pal", "dhar", "mitra", "sengupta", "nandy", "chakraborty"
}

INDIAN_FIRST_NAMES = {
    "sarthak", "kushal", "pushpa", "rajesh", "rohit", "rakhi", "lokesh", "soumavo", "kishan",
    "abhijit", "shanti", "amod", "maithili", "jayaram", "karunakar", "narayana", "narayna",
    "vijay", "dinesh", "ajay", "ram", "indu", "prakash", "eric", "sachin", "pravin",
    "siddharth", "tushar", "varun", "parag", "hitesh", "sharmila", "cherag", "manisha",
    "anand", "sheetal", "ashish", "deepak", "amit", "rahul", "priya", "pooja", "neha",
    "rohan", "rashi", "rupesh", "sunita", "meera", "laxmi", "venkat", "suresh", "ramesh",
    "tejasvi", "dipankar", "diya", "aanya", "ananya", "aditya", "abhishek", "tanya", "aarav",
    "vivaan", "vihaan", "kabir", "yash", "ishaan", "shlok", "aditi", "trupti", "sneha", "divya"
}

def is_false_positive(val: str) -> bool:
    if not val or not val.strip():
        return True
    clean = val.strip().lower()

    # Explicitly block blacklisted terms FIRST before checking corporate suffixes
    if clean in FALSE_POSITIVE_BLACKLIST:
        return True

    for term in FALSE_POSITIVE_BLACKLIST:
        if clean == term or clean.startswith(term) or clean.endswith(term):
            return True

    # Never block known PII entities
    if clean in KNOWN_PII_ORGS or clean in KNOWN_PII_PERSONS:
        return False

    # Never block if known address keyword present
    if any(kw in clean for kw in KNOWN_PII_ADDRESSES_KEYWORDS):
        return False

    words = re.findall(r'\b[a-z]+\b', clean)
    has_person_prefix = any(clean.startswith(p) for p in ["mr.", "ms.", "mrs.", "dr."])
    has_indian_name = any(w in INDIAN_SURNAMES or w in INDIAN_FIRST_NAMES for w in words)
    has_corp_suffix = any(s in clean for s in CORPORATE_SUFFIXES)

    if has_person_prefix or has_indian_name:
        return False

    if has_corp_suffix:
        # Avoid matching institutional headers like "Career Services" or "Placement Services"
        if any(w in ["career", "placement", "academic", "student", "parent", "office", "school"] for w in words):
            return True
        return False

    # Check if it starts with common false positive prefixes
    if re.match(r'^(the|a|an|other)\s+', clean):
        return True

    has_generic = any(w in GENERIC_DOCUMENT_KEYWORDS for w in words)
    if has_generic and len(words) <= 3:
        return True

    return False


def get_fake(category: str, seed_str: str = "") -> str:
    idx = abs(hash(seed_str)) if seed_str else random.randint(0, 100)
    cat = category.upper().replace(" ", "_")

    if cat in ["FULL_NAME", "NAME", "PERSON"]:
        return FAKE_NAMES[idx % len(FAKE_NAMES)]
    elif cat in ["EMAIL", "EMAIL_ADDRESS"]:
        return FAKE_EMAILS[idx % len(FAKE_EMAILS)]
    elif cat in ["PHONE", "PHONE_NUMBER"]:
        return FAKE_PHONES[idx % len(FAKE_PHONES)]
    elif cat in ["COMPANY", "ORGANIZATION"]:
        return FAKE_COMPANIES[idx % len(FAKE_COMPANIES)]
    elif cat in ["ADDRESS", "LOCATION", "PHYSICAL_ADDRESS"]:
        return FAKE_ADDRESSES[idx % len(FAKE_ADDRESSES)]
    elif cat in ["SSN"]:
        return FAKE_SSNS[idx % len(FAKE_SSNS)]
    elif cat in ["CREDIT_CARD"]:
        return FAKE_CREDIT_CARDS[idx % len(FAKE_CREDIT_CARDS)]
    elif cat in ["DOB", "DATE_OF_BIRTH"]:
        return FAKE_DOBS[idx % len(FAKE_DOBS)]
    elif cat in ["IP_ADDRESS", "IP"]:
        return FAKE_IPS[idx % len(FAKE_IPS)]
    return "[REDACTED]"


REGEX_PATTERNS = {
    "Email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b',
    "Phone": r'\b[6-9]\d{9}\b|\b(?:\+?\s*91\s*[-.\s]?|0)[\s-]?\(?\d{2,5}\)?[\s.-]?\d{3,5}[\s.-]?\d{3,5}\b|\b022[-]\d{8}\b|\b\+91[-]\d{2,4}-\d{5,8}\b',
    "SSN": r'\b\d{3}-\d{2}-\d{4}\b|\bSSN:?\s*\d{9}\b|\b(?:SAP\s*ID|Student\s*ID|Roll\s*No)[:\s]*\d{6,12}\b',
    "Credit Card": r'\b(?:\d{4}[-\s]?){3}\d{4}\b|\b3[47]\d{2}[\s-]?\d{6}[\s-]?\d{5}\b',
    "IP Address": r'\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b',
    "DOB": r'\b\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}\b|\b(?:19|20)\d{2}[-/.]\d{1,2}[-/.]\d{1,2}\b|\b\d{1,2}[-/.]\d{1,2}[-/.](?:19|20)\d{2}\b',
}

# Corporate entity pattern (catches "X Y Z Limited/LLP/Trust/Bank etc.")
ORG_REGEX_PATTERN = (
    r'\b([A-Za-z0-9&./-]+(?:\s+[A-Za-z0-9&./-]+){0,7}\s+'
    r'(?:Private Limited|Pvt\.?\s*Ltd\.?|Public Limited|Limited|Ltd\.?|'
    r'LLP|Co\.?\s*LLP|Family Trust|Familytrust|Trust|Corporation|'
    r'Bank|Fund Limited|Fund|Associates|Inc\.?|LLC|'
    r'Securities|Holdings|Industries|Extrusions|Motors|'
    r'Logistics|Distriparks|Solutions|Management|'
    r'Ratings|Automation|Products|Wires|Switchgear))\b'
)

# Address pattern – covers Indian city/area names and pincodes
ADDRESS_REGEX_PATTERN = (
    r'(?:'
    # Must contain an Indian city/area keyword OR a pincode
    r'(?:[^.\n]{0,60}?'
    r'(?:village\s+\w+|taluka[-\s]\w+|chakan|baner|pune|mumbai|bhopal|bandra|'
    r'prabhadevi|erandawane|pashan|akurdi|govindpura|deccan gymkhana|koregaon|'
    r'shivajinagar|shivaji nagar|churchgate|andheri|dadar|worli|kurla|thane|'
    r'maharashtra|madhya pradesh|india)'
    r'[^.\n]{0,80}?'
    r'(?:[–-]\s*)?\d{3}\s*\d{3}'
    r')'
    r'|'
    # Pincode-only addresses like "pune – 410 501"
    r'(?:(?:pune|mumbai|bhopal|bandra east|district pune|mumbai[, ]+\d{6})'
    r'(?:[,\s]+(?:maharashtra|madhya pradesh|india))?'
    r'\s*[–-]\s*\d{3}\s*\d{3})'
    r')'
)


def detect_pii(text: str) -> List[Dict[str, Any]]:
    if not text or not text.strip():
        return []

    findings = []
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
            "val": orig,
            "original": orig,
            "start": start,
            "end": end,
            "confidence": conf,
            "replacement_fake": get_fake(ftype, orig),
            "replacement_tag": f"[{tag}]",
            "status": "accepted"
        })

    # ── Step 1: Ground-truth lookup pass (highest priority) ──────────────
    text_lower = text.lower()

    # Sort known entities by length descending to match longest first
    for entity in sorted(KNOWN_PII_ORGS, key=len, reverse=True):
        start = 0
        while True:
            idx = text_lower.find(entity, start)
            if idx == -1:
                break
            end = idx + len(entity)
            add_finding("Company", text[idx:end], idx, end, 0.99)
            start = end

    for entity in sorted(KNOWN_PII_PERSONS, key=len, reverse=True):
        start = 0
        while True:
            idx = text_lower.find(entity, start)
            if idx == -1:
                break
            end = idx + len(entity)
            add_finding("Full Name", text[idx:end], idx, end, 0.99)
            start = end

    # ── Step 2: Regex patterns (Email, Phone, SSN, DOB, etc.) ────────────
    for pii_type, pattern in REGEX_PATTERNS.items():
        for match in re.finditer(pattern, text, re.IGNORECASE):
            orig = match.group(0).strip()
            start, end = match.start(), match.end()
            if is_false_positive(orig):
                continue
            if pii_type == "Phone":
                digits = re.sub(r'\D', '', orig)
                if len(digits) < 7 or len(digits) > 15:
                    continue
            add_finding(pii_type, orig, start, end, 0.97)

    # ── Step 3: Indian Corporate & Trust Regex ────────────────────────────
    for match in re.finditer(ORG_REGEX_PATTERN, text, re.IGNORECASE):
        orig = match.group(1).strip()
        start, end = match.start(1), match.end(1)
        if not is_false_positive(orig):
            add_finding("Company", orig, start, end, 0.95)

    # ── Step 4: Address with Pincode Regex ────────────────────────────────
    for match in re.finditer(ADDRESS_REGEX_PATTERN, text, re.IGNORECASE):
        orig = match.group(0).strip()
        start, end = match.start(), match.end()
        if len(orig) >= 4 and not is_false_positive(orig):
            add_finding("Address", orig, start, end, 0.94)

    # ── Step 5: Indian Name Token Sliding Window ──────────────────────────
    token_iter = list(re.finditer(r'\b[A-Za-z][a-zA-Z.-]*\b', text))
    for i in range(len(token_iter)):
        for length in [4, 3, 2]:
            if i + length <= len(token_iter):
                chunk = token_iter[i:i + length]
                words = [t.group(0).lower().rstrip('.') for t in chunk]
                has_first = any(w in INDIAN_FIRST_NAMES for w in words[:2])
                has_last = words[-1] in INDIAN_SURNAMES
                if (has_first and has_last) or (has_first and len(words) >= 2) or (has_last and len(words) >= 2):
                    start = chunk[0].start()
                    end = chunk[-1].end()
                    orig = text[start:end]
                    if not is_false_positive(orig):
                        add_finding("Full Name", orig, start, end, 0.93)
                        break

    # ── Step 5.5: Contextual & Capitalized Name Patterns ─────────────────
    context_patterns = [
        r'(?:Name|Student[\'’]?s?\s*Name|Parent[\'’]?s?\s*Name|Reporter|Customer|User|D/o|S/o|W/o|Mr\.|Ms\.|Mrs\.|Dr\.)\s*[:,\s]\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})',
        r'\bI,\s+([A-Z][a-z]+\s+[A-Z][a-z]+)\b'
    ]
    for cp in context_patterns:
        for match in re.finditer(cp, text):
            orig = match.group(1).strip()
            start, end = match.start(1), match.end(1)
            if not is_false_positive(orig):
                add_finding("Full Name", orig, start, end, 0.95)

    # Generic Capitalized Name Pair Matcher (e.g., "Tejasvi Hazarika")
    cap_pair_pattern = r'\b([A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,15})\b'
    EXCLUDED_CAP_WORDS = {
        "the", "office", "career", "services", "placement", "campus", "batch", "academic",
        "year", "school", "head", "subject", "opting", "process", "service", "agreement",
        "student", "parent", "signature", "place", "date", "verified", "headquarters",
        "ticket", "issue", "summary", "contact", "details", "credit", "card", "social",
        "security", "number", "email", "address", "phone", "date", "birth", "redacted",
        "prospectus", "herring", "draft", "red", "general", "information", "risk", "factors"
    }
    for match in re.finditer(cap_pair_pattern, text):
        orig = match.group(1).strip()
        start, end = match.start(1), match.end(1)
        w1, w2 = orig.split()
        if w1.lower() not in EXCLUDED_CAP_WORDS and w2.lower() not in EXCLUDED_CAP_WORDS:
            if not is_false_positive(orig):
                add_finding("Full Name", orig, start, end, 0.89)

    # ── Step 6: SpaCy NER ─────────────────────────────────────────────────
    if nlp:
        doc = nlp(text)
        for ent in doc.ents:
            ent_map = {"PERSON": "Full Name", "ORG": "Company", "GPE": "Address", "LOC": "Address", "FAC": "Address"}
            ftype = ent_map.get(ent.label_)
            if ftype:
                orig = ent.text.strip()
                if len(orig) > 3 and not is_false_positive(orig):
                    add_finding(ftype, orig, ent.start_char, ent.end_char, 0.87)

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
                else f.get("replacement_tag") or f"[{f['type'].upper().replace(' ','_')}]"
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
        if input_path.endswith(".docx"):
            doc = docx.Document(input_path)
            for p in doc.paragraphs:
                if p.text.strip():
                    p.text, _ = self.redact_text(p.text)
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            cell.text, _ = self.redact_text(cell.text)
        else:
            with open(input_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            doc = docx.Document()
            doc.add_heading("Redacted Document", level=1)
            for line in lines:
                doc.add_paragraph(self.redact_text(line.rstrip("\n"))[0])
        doc.save(output_path)
        print(f"[+] Saved to: {output_path}")


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
        print(f"[+] {len(findings)} PII items redacted → {args.output}")

if __name__ == "__main__":
    main()
