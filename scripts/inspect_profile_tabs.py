with open('my-node-app/templates/profile.html', encoding='utf-8') as f:
    for idx, line in enumerate(f, 1):
        if 'id="tab-' in line or 'class="tab-pane' in line or 'pagination' in line.lower():
            print(f"{idx}: {line.strip()[:100]}")
