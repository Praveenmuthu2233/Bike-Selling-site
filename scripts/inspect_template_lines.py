import glob
import sys

sys.stdout.reconfigure(encoding='utf-8')

for f in ['my-node-app/templates/admin.html', 'my-node-app/templates/adminAddListing.html', 'my-node-app/templates/contact.html', 'my-node-app/templates/profile.html', 'my-node-app/templates/sold-bike-details.html']:
    with open(f, encoding='utf-8', errors='ignore') as fp:
        for idx, line in enumerate(fp, 1):
            if any(t in line.lower() for t in ['hunter 350', 'dapper ash', 'classic 350']):
                print(f"{f}:{idx}: {line.strip()[:120]}")
