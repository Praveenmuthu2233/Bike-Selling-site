import subprocess

try:
    log = subprocess.check_output(['git', 'log', '-p', '-n', '10'], encoding='utf-8')
    for line in log.splitlines():
        if any(w in line for w in ['commit ', 'Author:', 'Date:', 'PASSWORD', 'TIDB', 'Clever', 'clever']):
            # avoid printing full password if sensitive, but print keys
            if 'PASS' in line:
                print(line.split('=')[0] + '=***')
            else:
                print(line[:100])
except Exception as e:
    print("Error:", e)
