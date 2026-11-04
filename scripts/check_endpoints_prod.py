import urllib.request
import json
import ssl

ctx = ssl.create_default_context()

for endpoint in ['/api/config', '/api/health', '/api/categories', '/api/notifications']:
    url = f'https://bike-selling-site-lco8.onrender.com{endpoint}'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            print(f'{endpoint}: {resp.status} -> {resp.read().decode()[:150]}')
    except urllib.error.HTTPError as e:
        print(f'{endpoint}: HTTP {e.code} -> {e.read().decode()[:150]}')
    except Exception as e:
        print(f'{endpoint}: Error -> {e}')
