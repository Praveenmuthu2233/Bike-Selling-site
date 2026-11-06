import glob
import re

files = ['my-node-app/templates/SoldOutPage.html', 'my-node-app/templates/bikeSelling.html', 'my-node-app/templates/about.html']
for fn in files:
    with open(fn, 'r', encoding='utf-8') as f:
        text = f.read()
    print("=== File:", fn)
    dark_matches = re.findall(r'#[0-9a-fA-F]{3,6}', text)
    print("  Hex colors count:", len(dark_matches))
    inline_styles = re.findall(r'style="[^"]*?"', text)
    print("  Inline styles count:", len(inline_styles))
