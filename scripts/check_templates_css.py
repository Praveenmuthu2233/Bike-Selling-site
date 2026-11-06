import glob, re

for f in sorted(glob.glob('my-node-app/templates/*.html')):
    c = open(f, encoding='utf-8', errors='ignore').read()
    links = re.findall(r'<link[^>]*stylesheet[^>]*>', c)
    styles = re.findall(r'<style[\s\S]*?</style>', c)
    print(f'=== {f} ===')
    for l in links:
        print('  LINK:', l)
    if styles:
        print(f'  INLINE STYLES: {len(styles)} block(s)')
