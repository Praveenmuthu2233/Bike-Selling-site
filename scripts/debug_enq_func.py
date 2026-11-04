with open('my-node-app/templates/profile.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('async function loadUserEnquiries')
if idx != -1:
    print("Found loadUserEnquiries at char", idx)
    print(repr(text[idx:idx+500]))
else:
    print("loadUserEnquiries not found")
