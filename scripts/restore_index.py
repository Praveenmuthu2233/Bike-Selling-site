import subprocess

def restore_index():
    out = subprocess.check_output(['git', 'show', 'bd8dfd4:my-node-app/templates/index.html'])
    with open('my-node-app/templates/index.html', 'wb') as f:
        f.write(out)
    print('Restored index.html from bd8dfd4')

if __name__ == '__main__':
    restore_index()
