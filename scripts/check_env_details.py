for p in ['.env', 'my-node-app/.env']:
    with open(p, 'r') as f:
        for line in f:
            if 'USER' in line or 'PASSWORD' in line or 'HOST' in line:
                if 'PASSWORD' in line:
                    k, v = line.strip().split('=', 1)
                    print(f"{p} -> {k}: repr={repr(v[:3])}... len={len(v)}")
                else:
                    print(f"{p} -> {line.strip()}")
