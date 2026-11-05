import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
for ep in ['/api/config', '/api/health']:
    try:
        url = 'https://bike-selling-site-lco8.onrender.com' + ep
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            data = json.loads(resp.read().decode())
            print(f"=== {ep} ===")
            print(json.dumps(data, indent=2))
    except Exception as e:
        print(f"Error {ep}:", e)
