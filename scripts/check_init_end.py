import re

with open('my-node-app/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Let's inspect where table creations end in initialize_database()
idx = content.find('CREATE TABLE IF NOT EXISTS `chat_read_status`')
if idx != -1:
    print(content[idx:idx+1000])
else:
    print("chat_read_status not found")
