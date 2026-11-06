with open('my-node-app/templates/sold-bike-details.html', 'r', encoding='utf-8') as f:
    text = f.read()

print("sold-bike-details.html length:", len(text), "lines:", len(text.splitlines()))
print(text[:1500])
