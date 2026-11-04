with open('my-node-app/templates/profile.html', 'r', encoding='utf-8') as f:
    text = f.read()

checks = [
    'user-sidebar-toggle-btn',
    'id="userSidebar"',
    'id="userSidebarBackdrop"',
    'id="my-listings-pagination"',
    'id="my-enquiries-pagination"',
    'id="favorites-pagination"',
    'id="user-negotiations-pagination"',
    'id="user-notifications-pagination"',
    'function toggleUserSidebar(',
    'const userPages =',
    'function changeUserPage(',
    'function changeUserLimit(',
    'function renderUserPagination(',
    'loadUserListings(page = 1, status = currentUserListingFilter, limit = null)',
    'loadUserNegotiations(page = 1, limit = null)',
    'loadUserEnquiries(page = 1, limit = null)',
    'loadFavorites(page = 1, limit = null)',
    'loadUserNotifications(page = 1, limit = null)'
]

all_ok = True
for c in checks:
    present = c in text
    print(f"[{'OK' if present else 'FAIL'}] {c}")
    if not present:
        all_ok = False

if all_ok:
    print("\nALL PROFILE.HTML CHECKS PASSED!")
else:
    print("\nSOME CHECKS FAILED!")
