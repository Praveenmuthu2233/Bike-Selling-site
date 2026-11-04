import glob
import sys

sys.stdout.reconfigure(encoding='utf-8')

for f in glob.glob('my-node-app/templates/*.html'):
    with open(f, encoding='utf-8', errors='ignore') as fp:
        content = fp.read()
        for term in ['classic 350', 'hunter 350', 'dapper ash', 'review-1', 'review-2', 'rahul sharma', 'anand kumar', 'priya', 'sample', 'dummy']:
            if term in content.lower():
                print(f"Found '{term}' in {f}")
