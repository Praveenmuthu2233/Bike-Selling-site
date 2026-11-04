import os

for fname in ['enquiryBike.html', 'enquiry-bike-details.html', 'bikeSelling.html', 'profile.html']:
    fpath = os.path.join('my-node-app', 'templates', fname)
    if os.path.exists(fpath):
        with open(fpath, 'r', encoding='utf-8') as f:
            text = f.read()
        print(f"\n=== {fname} ===")
        for idx, line in enumerate(text.splitlines(), 1):
            if 'mock' in line.lower() or 'demo rider' in line.lower() or 'fake' in line.lower():
                print(f"L{idx}: {line[:100]}")
