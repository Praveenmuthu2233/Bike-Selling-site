with open('my-node-app/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

idx = content.find('CREATE TABLE IF NOT EXISTS `durable_images`')
print(content[idx:idx+1500])
