import redact_pii

test_text = """
1. Full Name: Rashi Patil and Rohan Dey, also Tejasvi Hazarika and Dipankar Hazarika.
2. Email: rashhi.patil@gmail.com and rohan.dey@gmail.com
3. Phone: +91 9876543210 and 9999069169
4. Company: Acme Solutions Pvt Ltd, KSH International Limited and HDFC Bank
5. Address: 17 Market Street, Mumbai - 400001, Maharashtra
6. SSN / Student ID: 987-65-4321 and SAP ID: 500119060
7. Credit Card: 4532-7192-8834-1102
8. DOB / Date: 1992-11-05 and 28 April 2026
9. IP Address: 192.168.1.105
"""

findings = redact_pii.detect_pii(test_text)
print(f"Total Detected PII Items: {len(findings)}")
for f in findings:
    print(f"{f['type']}: '{f['original']}' -> '{f['replacement_fake']}'")
