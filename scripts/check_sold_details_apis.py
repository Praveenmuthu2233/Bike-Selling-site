with open('my-node-app/templates/sold-bike-details.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
sections = re.findall(r'<div[^>]*class=[\'\"]([^\'\"]*section[^\'\"]*|panel[^\'\"]*|card[^\'\"]*)[\'\"]', text)
print("Sections found in sold-bike-details.html:", len(sections))

apis = re.findall(r'/api/[a-zA-Z0-9_\-\/]+', text)
print("APIs called in sold-bike-details.html:", set(apis))
