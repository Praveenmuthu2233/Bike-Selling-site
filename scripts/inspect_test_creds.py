with open('tests/test_tidb_real_data_integration.py', 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f, 1):
        if any(w in line for w in ['TIDB', 'DB_', 'password', 'user', 'connect', 'host']):
            print(f"{idx}: {line.strip()[:100]}")
