with open('my-node-app/templates/profile.html', 'r', encoding='utf-8') as f:
    text = f.read()

checks = [
    'id="my-listings-pagination"',
    'id="my-enquiries-table-body"',
    'id="favorites-grid"',
    'id="user-negotiations-container"',
    'id="user-notifications-list"',
    'async function loadUserListings(',
    'async function loadUserNegotiations(',
    'async function loadFavorites(',
    'async function loadUserEnquiries(',
    'async function loadUserNotifications('
]
for c in checks:
    print(c, '-> FOUND' if c in text else '-> NOT FOUND')
