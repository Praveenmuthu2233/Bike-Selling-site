import os
import re

admin_html_path = 'my-node-app/templates/admin.html'
with open(admin_html_path, 'r', encoding='utf-8') as f:
    text = f.read()

styles = re.findall(r'<style[^>]*>(.*?)</style>', text, re.DOTALL)
print(f"admin.html has {len(styles)} style blocks")
for i, s in enumerate(styles):
    print(f"Block {i} length: {len(s)}")
    if 'chat' in s.lower():
        print(f"  Contains 'chat' keywords!")

# Also check adminModern.css
css_path = 'my-node-app/static/adminModern.css'
with open(css_path, 'r', encoding='utf-8') as f:
    css = f.read()
chat_rules = [line for line in css.splitlines() if 'chat' in line.lower()][:15]
print(f"adminModern.css chat references: {len(chat_rules)}")
for l in chat_rules[:5]:
    print("  ", l)
