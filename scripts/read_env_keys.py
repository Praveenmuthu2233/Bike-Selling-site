with open('my-node-app/.env', 'r', encoding='utf-8') as f:
    for line in f:
        if any(k in line for k in ['HOST', 'PORT', 'USER', 'DATABASE', 'DB', 'TIDB']):
            # mask password if any
            if 'PASS' in line:
                print(line.split('=')[0] + '=***')
            else:
                print(line.strip())
