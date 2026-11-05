import subprocess

out = subprocess.check_output(['git', 'show', '7d5b6680246b1c5142bc95bc3cd137bef95125b6'], encoding='utf-8')
for l in out.splitlines()[:60]:
    print(l)
