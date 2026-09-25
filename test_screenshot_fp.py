import redact_pii

prospectus_text = """
The Equity Shares have not been recommended or approved by the Securities and Exchange Board of India.
Qualified Institutional Buyers and Retail Individual Bidders should review the document.
Promoter Selling Shareholders will participate in the offer.
The Cap Price and Floor Price will be decided by Our Company and the Book Running Lead Managers.
Book Building Process details are given in the prospectus.
GENERAL RISKS: Investments in equity and equity-related securities involve a high degree of risk.
The Equity Shares are proposed to be listed on the BSE Limited and National Stock Exchange of India Limited.

Contact Details of Real PII:
Name: Rashi Patil
Email: rashhi.patil@gmail.com
Phone: +91 9876543210
Company: KSH International Limited
I, Tejasvi Hazarika am applying for the placement.
"""

findings = redact_pii.detect_pii(prospectus_text)
print(f"Total Detected PII Items: {len(findings)}")
for f in findings:
    print(f"[{f['type']}] '{f['original']}' -> '{f['replacement_fake']}'")
