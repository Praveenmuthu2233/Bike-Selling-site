with open('my-node-app/app.py', 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f, 1):
        if '/api/chat' in line or 'chat_messages' in line or 'chat_conversations' in line:
            print(f'{idx}: {line.strip()[:100]}')
