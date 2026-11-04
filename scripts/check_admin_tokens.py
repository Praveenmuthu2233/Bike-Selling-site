with open('my-node-app/templates/admin.html', 'r', encoding='utf-8') as f:
    text = f.read()

checks = [
    'function renderPagination(containerId, p, loadFnName)',
    "renderPagination('bikes-pagination', res.pagination, 'loadAdminBikes');",
    "renderPagination('soldout-bikes-pagination', res.pagination, 'loadSoldOutBikesView');",
    "renderPagination('enquiries-pagination', res.pagination, 'loadAdminEnquiries');",
    "renderPagination('users-pagination', res.pagination, 'loadAdminUsers');",
    'id="admin-staff-tbody"',
    'id="admin-messages-tbody"',
    'id="staff-activity-list"'
]
for c in checks:
    print(c, '-> FOUND' if c in text else '-> NOT FOUND')
