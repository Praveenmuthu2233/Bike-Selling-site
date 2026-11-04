with open('.env') as f1, open('my-node-app/.env') as f2:
    lines1 = {l.split('=', 1)[0].strip(): l.split('=', 1)[1].strip() for l in f1 if '=' in l}
    lines2 = {l.split('=', 1)[0].strip(): l.split('=', 1)[1].strip() for l in f2 if '=' in l}

for k in ['DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT', 'DB_NAME']:
    v1 = lines1.get(k)
    v2 = lines2.get(k)
    print(f"{k}: equal={v1 == v2}, len1={len(v1) if v1 else 0}, len2={len(v2) if v2 else 0}")
    if k == 'DB_PASSWORD':
        print(f"  v1 hash: {hash(v1)}, v2 hash: {hash(v2)}")
