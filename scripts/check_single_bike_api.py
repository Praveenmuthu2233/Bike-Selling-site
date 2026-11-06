with open('my-node-app/app.py', 'r', encoding='utf-8') as f:
    code = f.read()

idx = code.find('def get_single_bike_api(bike_id):')
print(code[idx:idx+1500])
