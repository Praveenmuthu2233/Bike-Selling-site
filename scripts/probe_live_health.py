import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

urls = [
    "https://bike-selling-site-lco8.onrender.com/api/health",
    "https://bike-selling-site-lco8.onrender.com/api/config",
    "https://bike-selling-site-lco8.onrender.com/health",
    "https://bike-selling-site-lco8.onrender.com/api/bikes?page=1&limit=5"
]

for url in urls:
    print(f"--- Probing {url} ---")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            body = resp.read().decode("utf-8")
            print(f"HTTP {resp.status}")
            try:
                data = json.loads(body)
                print(json.dumps(data, indent=2))
            except Exception:
                print(body[:500])
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}")
        try:
            body = e.read().decode("utf-8")
            data = json.loads(body)
            print(json.dumps(data, indent=2))
        except Exception:
            print(e)
    except Exception as e:
        print(f"Error: {e}")
