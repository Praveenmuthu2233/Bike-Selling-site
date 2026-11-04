with open('my-node-app/templates/profile.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

targets = [
    'async function loadUserListings',
    'async function loadUserNegotiations',
    'async function respondNegotiation',
    'async function loadUserEnquiries',
    'async function loadFavorites',
    'async function loadUserNotifications',
    'async function markAllUserNotificationsRead'
]

for t in targets:
    for i, line in enumerate(lines):
        if t in line:
            print(f"{t} is at Line {i+1}")
