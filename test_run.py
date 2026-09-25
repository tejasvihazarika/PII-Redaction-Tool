import redact_pii

lines = [
    "ORG\tksh international limited\tSoylent Technologies Limited",
    "ADDRESS\t11/4 and 11/5 village birdewadi chakan taluka - khed pune – 410 501\t73, Willow Park, Springfield – 410 001, Sample State, India",
    "ADDRESS\tbaner pune – 411 045\t23, Cedar Street, Rivertown – 411 002, Sample State, India",
    "PERSON\tsarthak malvadkar\tAnita Kapoor",
    "EMAIL\tcs.connect@kshinternational.com\tanita.doe@example.com",
    "PHONE\t+ 91 20 45053237\t+91 19938 03577",
    "PERSON\tkushal subbayya hegde\tLila Stone",
    "PERSON\tpushpa kushal hegde\tAlex Reyes",
    "PERSON\trajesh kushal hegde\tAlex Verma",
    "PERSON\trohit kushal hegde\tSara Doe",
    "PERSON\trakhi girija shetty\tKaran Mehta",
    "ORG\tdhaulagiri family trust\tNorthwind Industries Limited",
    "ORG\teverest family trust\tSoylent Technologies Limited 2",
    "ORG\twaterloo industrial park vi private limited\tHooli Bank Limited",
    "ORG\tpandit llp\tHooli Bank Limited 2",
    "ORG\tnuvama wealth management limited\tStark Securities Limited 2",
    "PERSON\tlokesh shah\tDavid Bose",
    "PERSON\tsoumavo sarkar\tAlex Walsh",
    "EMAIL\tksh.ipo@nuvama.com\tmary.fox@example.com",
    "PHONE\t+91 22 4009 4400\t+91 10444 74271",
    "ORG\ticici securities limited\tAcme Holdings Limited 2",
    "PERSON\tkishan rastogi\tMary Bright",
    "PERSON\tabhijit diwan\tOscar Brooks",
    "EMAIL\tksh@icicisecurities.com\tkaran.rivera@example.com",
    "PHONE\t+91 22 6807 7100\t+91 18199 42055",
    "ORG\tmufg intime india private limited\tGlobex Capital Limited",
    "PERSON\tshanti gopalkrishnan\tPeter Mehta",
    "PHONE\t+91 81081 14949\t+91 11606 02295",
    "EMAIL\tkshinternational.ipo@in.mpms.mufg.com\tkaran.brooks@example.com",
    "ORG\tbhandary metal extrusion private limited\tInitech Solutions Private Limited",
    "ADDRESS\t11/3, 11/4 and 11/5, village birdewadi, chakan taluka - khed, pune – 410 501, maharashtra, india\t84, Birch Lane, Lakeview – 400 003, Sample State, India",
    "ADDRESS\t201, tower 2, montreal business centre, off pallod farms, baner, pune – 411 045, maharashtra, india\t45, Maple Avenue, Lakeview – 400 003, Sample State, India",
    "ADDRESS\t801 - 804, wing a, building no 3, inspire bkc, g block, bandra kurla complex, bandra east, mumbai 400051, maharashtra, india\t25, Maple Avenue, Springfield – 410 001, Sample State, India",
    "ADDRESS\ticici venture house, appasaheb marathe marg, prabhadevi, mumbai 400025, maharashtra, india\t38, Willow Park, Rivertown – 411 002, Sample State, India",
    "PERSON\tamod joshi\tNoah Bright",
    "ORG\thdfc bank limited\tVandelay Exports Limited 4",
    "ORG\tcare ratings limited\tAcme Holdings Limited 5",
    "PERSON\tmaithili rajesh hegde\tMary Brooks",
    "PERSON\tram kumar tiwari\tOwen Osei",
    "PERSON\tindu jacob\tLila Mehta",
    "PERSON\tprakash boricha\tOscar Smith",
    "PERSON\teric bacha\tPeter Doe",
    "PERSON\tsachin gawade\tSara Quinn",
    "PERSON\tpravin teli\tNoah Fox",
    "PERSON\tsiddharth jadhav\tLila Smith",
    "PERSON\ttushar gavankar\tOscar Stone",
    "PERSON\thitesh ramani\tNina Walsh",
    "PERSON\tsharmila joshi\tRaj Fox",
    "PERSON\tcherag gyara\tOscar Verma",
    "PERSON\tmanisha shukla\tAnita Brooks",
    "PERSON\tanand soni\tMary Reyes",
    "ORG\tbajaj finance limited\tSoylent Technologies Limited 9"
]

passed = 0
failed = 0

for line in lines:
    parts = line.split('\t')
    if len(parts) >= 2:
        cat = parts[0]
        val = parts[1].strip()
        findings = redact_pii.detect_pii(val)
        if len(findings) > 0:
            passed += 1
        else:
            print(f"[FAIL] Category: {cat} | Value: '{val}'")
            failed += 1

print(f"\nRESULTS: Passed = {passed} / {passed + failed} ({(passed/(passed+failed))*100:.1f}%)")
