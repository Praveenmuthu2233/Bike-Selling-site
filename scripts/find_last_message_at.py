import os

def search_last_message_at():
    for root, dirs, files in os.walk('.'):
        if '.git' in root or 'node_modules' in root:
            continue
        for f in files:
            if f.endswith(('.py', '.sql', '.js', '.html')):
                path = os.path.join(root, f)
                try:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as fp:
                        for i, line in enumerate(fp, 1):
                            if 'last_message_at' in line:
                                print(f'{path}:{i}: {line.strip()}')
                except Exception as e:
                    pass

if __name__ == '__main__':
    search_last_message_at()
