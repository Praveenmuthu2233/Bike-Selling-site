for path in ['.env', 'my-node-app/.env']:
    print(f"=== {path} ===")
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line_s = line.strip()
            if not line_s or line_s.startswith('#'): continue
            k = line_s.split('=')[0]
            if 'PASS' in k or 'SECRET' in k:
                val = line_s.split('=', 1)[1]
                print(f"{k} = len({len(val)}) [{val[:2]}...{val[-2:]}]")
            else:
                print(line_s)
