import subprocess

out = subprocess.check_output(['git', 'show', 'HEAD:my-node-app/templates/profile.html'], encoding='utf-8')
with open('my-node-app/templates/profile.html', 'w', encoding='utf-8') as f:
    f.write(out)
print('Restored profile.html successfully!')
