with open('my-node-app/templates/admin.html', 'r', encoding='utf-8') as f:
    text = f.read()

checks = [
    'id="bikes-pagination"',
    'id="soldout-bikes-pagination"',
    'id="enquiries-pagination"',
    'id="users-pagination"',
    'id="staff-pagination"',
    'id="staff-activity-pagination"',
    'id="messages-pagination"',
    'const adminPages =',
    'function changeAdminPage(',
    'function changeAdminLimit(',
    'function renderPagination(containerId, sectionOrPagination, pMaybe)',
    "loadAdminBikes(tab = 'all', page = 1, limit = null)",
    "loadSoldOutBikesView(page = 1, limit = null)",
    "loadAdminEnquiries(tab = 'all', page = 1, limit = null)",
    "loadAdminUsers(tab = 'all', page = 1, limit = null)",
    "loadAdminStaff(page = 1, limit = null)",
    "loadStaffActivity(page = 1, limit = null)",
    "loadAdminMessages(page = 1, limit = null)"
]

all_ok = True
for c in checks:
    present = c in text
    print(f"[{'OK' if present else 'FAIL'}] {c}")
    if not present:
        all_ok = False

if all_ok:
    print("\nALL ADMIN.HTML CHECKS PASSED!")
else:
    print("\nSOME CHECKS FAILED!")
