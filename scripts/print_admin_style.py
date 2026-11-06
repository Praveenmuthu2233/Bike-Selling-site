with open('my-node-app/templates/admin.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
m = re.search(r'<style[^>]*>(.*?)</style>', text, re.DOTALL)
if m:
    lines = m.group(1).splitlines()
    for l in lines[:60]:
        print(l)
