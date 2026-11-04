# -*- coding: utf-8 -*-
"""
Patch Admin Panel and User Panel with responsive navigation and server-side pagination.
"""
import os
import re

ADMIN_HTML = 'my-node-app/templates/admin.html'
PROFILE_HTML = 'my-node-app/templates/profile.html'

def patch_admin():
    print(f"Reading {ADMIN_HTML}...")
    with open(ADMIN_HTML, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Add #staff-pagination in #tab-staff if not present
    if 'id="staff-pagination"' not in content:
        target = 'id="admin-staff-tbody">\n                <tr><td colspan="7" style="text-align:center; padding:2rem;"><i class="fas fa-spinner fa-spin"></i> Loading staff list...</td></tr>\n              </tbody>\n            </table>\n          </div>'
        replacement = target + '\n          <!-- Staff Pagination -->\n          <div class="pagination-container" id="staff-pagination"></div>'
        if target in content:
            content = content.replace(target, replacement, 1)
            print("Added #staff-pagination.")
        else:
            # Try with \r\n
            target_crlf = target.replace('\n', '\r\n')
            replacement_crlf = replacement.replace('\n', '\r\n')
            if target_crlf in content:
                content = content.replace(target_crlf, replacement_crlf, 1)
                print("Added #staff-pagination (CRLF).")
            else:
                print("WARNING: Could not find target for #staff-pagination")

    # 2. Add #staff-activity-pagination in #tab-staff if not present
    if 'id="staff-activity-pagination"' not in content:
        target = '<div id="staff-activity-list" style="display:flex; flex-direction:column; gap:0.75rem;">\n                <div style="text-align:center; padding:1rem; color:var(--admin-text-secondary); font-size:0.85rem;">\n                  <i class="fas fa-spinner fa-spin"></i> Loading staff activity...\n                </div>\n              </div>\n            </div>\n          </div>'
        replacement = '<div id="staff-activity-list" style="display:flex; flex-direction:column; gap:0.75rem;">\n                <div style="text-align:center; padding:1rem; color:var(--admin-text-secondary); font-size:0.85rem;">\n                  <i class="fas fa-spinner fa-spin"></i> Loading staff activity...\n                </div>\n              </div>\n              <!-- Staff Activity Pagination -->\n              <div class="pagination-container" id="staff-activity-pagination" style="margin-top:1rem;"></div>\n            </div>\n          </div>'
        if target in content:
            content = content.replace(target, replacement, 1)
            print("Added #staff-activity-pagination.")
        else:
            target_crlf = target.replace('\n', '\r\n')
            replacement_crlf = replacement.replace('\n', '\r\n')
            if target_crlf in content:
                content = content.replace(target_crlf, replacement_crlf, 1)
                print("Added #staff-activity-pagination (CRLF).")
            else:
                print("WARNING: Could not find target for #staff-activity-pagination")

    # 3. Add #messages-pagination in #tab-messages if not present
    if 'id="messages-pagination"' not in content:
        target = '<tbody id="admin-messages-tbody">\n                <tr><td colspan="6" style="text-align:center; padding:2rem;"><i class="fas fa-spinner fa-spin"></i> Loading contact messages...</td></tr>\n              </tbody>\n            </table>\n          </div>\n        </section>'
        replacement = '<tbody id="admin-messages-tbody">\n                <tr><td colspan="6" style="text-align:center; padding:2rem;"><i class="fas fa-spinner fa-spin"></i> Loading contact messages...</td></tr>\n              </tbody>\n            </table>\n          </div>\n          <!-- Contact Messages Pagination -->\n          <div class="pagination-container" id="messages-pagination"></div>\n        </section>'
        if target in content:
            content = content.replace(target, replacement, 1)
            print("Added #messages-pagination.")
        else:
            target_crlf = target.replace('\n', '\r\n')
            replacement_crlf = replacement.replace('\n', '\r\n')
            if target_crlf in content:
                content = content.replace(target_crlf, replacement_crlf, 1)
                print("Added #messages-pagination (CRLF).")
            else:
                print("WARNING: Could not find target for #messages-pagination")

    # 4. Replace renderPagination function with universal version
    old_pag_pattern = r'// Pagination Component\s+function renderPagination\s*\([^)]*\)\s*\{[\s\S]*?\}\s*// Outside click listeners'
    new_pag_code = '''// ==================================================
    // Universal Admin Pagination Component & State
    // ==================================================
    const adminPages = {
      bikes: { page: 1, limit: 10 },
      soldout: { page: 1, limit: 10 },
      enquiries: { page: 1, limit: 10 },
      users: { page: 1, limit: 10 },
      staff: { page: 1, limit: 10 },
      messages: { page: 1, limit: 10 },
      audit: { page: 1, limit: 10 }
    };

    function changeAdminPage(section, newPage) {
      if (!adminPages[section]) adminPages[section] = { page: 1, limit: 10 };
      adminPages[section].page = Math.max(1, newPage);
      if (section === 'bikes') loadAdminBikes(currentBikeTab, adminPages.bikes.page, adminPages.bikes.limit);
      else if (section === 'soldout') loadSoldOutBikesView(adminPages.soldout.page, adminPages.soldout.limit);
      else if (section === 'enquiries') loadAdminEnquiries(currentEnquiryTab, adminPages.enquiries.page, adminPages.enquiries.limit);
      else if (section === 'users') loadAdminUsers(currentUserTab, adminPages.users.page, adminPages.users.limit);
      else if (section === 'staff') loadAdminStaff(adminPages.staff.page, adminPages.staff.limit);
      else if (section === 'messages') loadAdminMessages(adminPages.messages.page, adminPages.messages.limit);
      else if (section === 'audit') loadStaffActivity(adminPages.audit.page, adminPages.audit.limit);
    }

    function changeAdminLimit(section, newLimit) {
      newLimit = parseInt(newLimit, 10) || 10;
      if (!adminPages[section]) adminPages[section] = { page: 1, limit: 10 };
      adminPages[section].limit = newLimit;
      adminPages[section].page = 1;
      changeAdminPage(section, 1);
    }

    function renderPagination(containerId, sectionOrPagination, pMaybe) {
      const c = document.getElementById(containerId);
      if (!c) return;
      let section = 'bikes';
      let p = null;
      if (typeof sectionOrPagination === 'string') {
        section = sectionOrPagination;
        p = pMaybe;
      } else {
        p = sectionOrPagination;
        if (containerId.includes('bikes')) section = 'bikes';
        else if (containerId.includes('soldout')) section = 'soldout';
        else if (containerId.includes('enquiries')) section = 'enquiries';
        else if (containerId.includes('users')) section = 'users';
        else if (containerId.includes('staff-activity')) section = 'audit';
        else if (containerId.includes('staff')) section = 'staff';
        else if (containerId.includes('messages')) section = 'messages';
      }

      if (!p || p.total === 0) {
        c.innerHTML = '';
        return;
      }

      const curr = p.page || 1;
      const limit = p.limit || adminPages[section]?.limit || 10;
      const total = p.total || 0;
      const totalPages = p.totalPages || p.total_pages || Math.ceil(total / limit) || 1;
      const start = (p.start !== undefined && p.start !== null) ? p.start : ((curr - 1) * limit + 1);
      const end = (p.end !== undefined && p.end !== null) ? p.end : Math.min(curr * limit, total);

      let pageButtons = [];
      const maxButtons = 5;
      let startPage = Math.max(1, curr - 2);
      let endPage = Math.min(totalPages, startPage + maxButtons - 1);
      if (endPage - startPage < maxButtons - 1) {
        startPage = Math.max(1, endPage - maxButtons + 1);
      }

      if (startPage > 1) {
        pageButtons.push(`<button type="button" class="btn-page" onclick="changeAdminPage('${section}', 1)">1</button>`);
        if (startPage > 2) pageButtons.push(`<span class="page-ellipsis">&hellip;</span>`);
      }

      for (let i = startPage; i <= endPage; i++) {
        pageButtons.push(`
          <button type="button" class="btn-page ${i === curr ? 'active' : ''}" onclick="changeAdminPage('${section}', ${i})" ${i === curr ? 'aria-current="page"' : ''}>
            ${i}
          </button>
        `);
      }

      if (endPage < totalPages) {
        if (endPage < totalPages - 1) pageButtons.push(`<span class="page-ellipsis">&hellip;</span>`);
        pageButtons.push(`<button type="button" class="btn-page" onclick="changeAdminPage('${section}', ${totalPages})">${totalPages}</button>`);
      }

      c.innerHTML = `
        <div class="pagination-wrapper">
          <div class="pagination-info">
            Showing <strong>${start}&ndash;${end}</strong> of <strong>${total}</strong> records
          </div>
          <div class="pagination-controls">
            <label class="pagination-limit-label" style="display:inline-flex; align-items:center; gap:6px; font-size:0.84rem; color:var(--admin-text-secondary); margin-right:6px;">
              Rows:
              <select class="pagination-limit-select" onchange="changeAdminLimit('${section}', this.value)">
                <option value="10" ${limit === 10 ? 'selected' : ''}>10</option>
                <option value="25" ${limit === 25 ? 'selected' : ''}>25</option>
                <option value="50" ${limit === 50 ? 'selected' : ''}>50</option>
              </select>
            </label>
            <button type="button" class="btn-page" ${curr <= 1 ? 'disabled' : ''} onclick="changeAdminPage('${section}', ${curr - 1})" title="Previous Page">
              <i class="fas fa-chevron-left"></i>
            </button>
            <div class="pagination-pages" style="display:inline-flex; gap:4px;">
              ${pageButtons.join('')}
            </div>
            <button type="button" class="btn-page" ${curr >= totalPages ? 'disabled' : ''} onclick="changeAdminPage('${section}', ${curr + 1})" title="Next Page">
              <i class="fas fa-chevron-right"></i>
            </button>
          </div>
        </div>
      `;
    }

    // Outside click listeners'''

    match = re.search(old_pag_pattern, content)
    if match:
        content = content[:match.start()] + new_pag_code + content[match.end():]
        print("Replaced renderPagination in admin.html.")
    else:
        print("WARNING: Could not match old_pag_pattern")

    # 5. Update loadAdminBikes signature and limit parameter
    content = content.replace("async function loadAdminBikes(tab = 'all', page = 1) {", "async function loadAdminBikes(tab = 'all', page = 1, limit = null) {\n      limit = limit || adminPages.bikes.limit || 10;")
    content = content.replace("let url = `/api/admin/bikes?page=${page}&limit=10&tab=${tab}&sort=${sort}`;", "let url = `/api/admin/bikes?page=${page}&limit=${limit}&tab=${tab}&sort=${sort}`;")
    content = content.replace("renderPagination('bikes-pagination', res.pagination, 'loadAdminBikes');", "renderPagination('bikes-pagination', 'bikes', res.pagination);")

    # 6. Update loadSoldOutBikesView signature and limit parameter
    content = content.replace("async function loadSoldOutBikesView(page = 1) {", "async function loadSoldOutBikesView(page = 1, limit = null) {\n      limit = limit || adminPages.soldout.limit || 10;")
    content = content.replace("const params = new URLSearchParams({ page: page, limit: 10 });", "const params = new URLSearchParams({ page: page, limit: limit });")
    content = content.replace("renderPagination('soldout-bikes-pagination', res.pagination, 'loadSoldOutBikesView');", "renderPagination('soldout-bikes-pagination', 'soldout', res.pagination);")

    # 7. Update loadAdminEnquiries signature and limit parameter
    content = content.replace("async function loadAdminEnquiries(tab = 'all', page = 1) {", "async function loadAdminEnquiries(tab = 'all', page = 1, limit = null) {\n      limit = limit || adminPages.enquiries.limit || 10;")
    content = content.replace("let url = `/api/admin/enquiries?page=${page}&limit=10&tab=${tab}`;", "let url = `/api/admin/enquiries?page=${page}&limit=${limit}&tab=${tab}`;")
    content = content.replace("renderPagination('enquiries-pagination', res.pagination, 'loadAdminEnquiries');", "renderPagination('enquiries-pagination', 'enquiries', res.pagination);")

    # 8. Update loadAdminUsers signature and limit parameter
    content = content.replace("async function loadAdminUsers(tab = 'all', page = 1) {", "async function loadAdminUsers(tab = 'all', page = 1, limit = null) {\n      limit = limit || adminPages.users.limit || 10;")
    content = content.replace("let url = `/api/admin/users?page=${page}&limit=10&tab=${tab}`;", "let url = `/api/admin/users?page=${page}&limit=${limit}&tab=${tab}`;")
    content = content.replace("renderPagination('users-pagination', res.pagination, 'loadAdminUsers');", "renderPagination('users-pagination', 'users', res.pagination);")

    # 9. Update loadAdminStaff to support page, limit, and pagination
    old_staff_func_pattern = r'// Staff Management\s+async function loadAdminStaff\(\)\s*\{[\s\S]*?loadStaffActivity\(\);\s*\}\s*catch\s*\(err\)\s*\{[\s\S]*?\}\s*\}'
    new_staff_func = '''// Staff Management
    async function loadAdminStaff(page = 1, limit = null) {
      limit = limit || adminPages.staff.limit || 10;
      const tbody = document.getElementById('admin-staff-tbody');
      if (!tbody) return;
      tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:2rem;"><i class="fas fa-spinner fa-spin"></i> Loading staff...</td></tr>';

      try {
        const res = await apiRequest(`/api/admin/staff?page=${page}&limit=${limit}`);
        const staff = res.data || [];

        if (staff.length === 0) {
          tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:2rem; color:var(--admin-text-secondary);">No staff records found.</td></tr>';
          renderPagination('staff-pagination', 'staff', res.pagination);
          return;
        }

        tbody.innerHTML = staff.map(s => {
          const isSuper = s.role === 'superadmin';
          const isActive = s.is_active !== 0 && s.is_active !== false;
          return `
            <tr>
              <td data-label="Staff Member">
                <div style="display:flex; align-items:center; gap:0.65rem;">
                  <div style="width:34px; height:34px; border-radius:var(--radius-sm); background:${isSuper ? 'var(--admin-primary)' : '#374151'}; color:#fff; display:flex; align-items:center; justify-content:center; font-weight:700;">
                    ${(s.full_name || s.username || 'A').charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <strong>${s.full_name || s.username}</strong>
                  </div>
                </div>
              </td>
              <td data-label="Username"><code>${s.username}</code></td>
              <td data-label="Email & Phone">${s.email || ''}<br><span style="font-size:0.75rem; color:var(--admin-text-secondary);">${s.phone || ''}</span></td>
              <td data-label="Role"><span class="badge-status ${isSuper ? 'badge-approved' : 'badge-sold'}">${s.role}</span></td>
              <td data-label="Status"><span class="badge-status ${isActive ? 'badge-approved' : 'badge-rejected'}">${isActive ? 'Active' : 'Inactive'}</span></td>
              <td data-label="Last Login"><span style="font-size:0.8rem; color:var(--admin-text-secondary);">${(s.last_login || 'Never').substring(0, 16).replace('T', ' ')}</span></td>
              <td data-label="Actions" style="text-align:right;">
                <div class="table-action-group">
                  <button class="btn-table-action" onclick="openEditStaffModal(${s.id})" title="Edit Details"><i class="fas fa-edit"></i></button>
                  <button class="btn-table-action ${isActive ? 'danger' : 'success'}" onclick="toggleStaffStatusAction(${s.id}, ${isActive ? 0 : 1})">
                    ${isActive ? 'Deactivate' : 'Activate'}
                  </button>
                  ${s.username !== 'admin' ? `
                    <button class="btn-table-action danger" onclick="deleteStaffAction(${s.id})" title="Delete Staff"><i class="fas fa-trash"></i></button>
                  ` : ''}
                </div>
              </td>
            </tr>
          `;
        }).join('');

        renderPagination('staff-pagination', 'staff', res.pagination);

      } catch (err) {
        tbody.innerHTML = `<tr><td colspan="7" style="color:red; text-align:center;">${err.message}</td></tr>`;
      }
    }'''
    match = re.search(old_staff_func_pattern, content)
    if match:
        content = content[:match.start()] + new_staff_func + content[match.end():]
        print("Updated loadAdminStaff.")
    else:
        print("WARNING: Could not match old_staff_func_pattern")

    # 10. Update loadStaffActivity to support page, limit, and pagination
    old_activity_pattern = r'async function loadStaffActivity\(\)\s*\{[\s\S]*?c\.innerHTML\s*=\s*acts\.slice\(0,\s*8\)[\s\S]*?\}\s*catch\s*\(e\)\s*\{[\s\S]*?\}\s*\}'
    new_activity_func = '''async function loadStaffActivity(page = 1, limit = null) {
      limit = limit || adminPages.audit.limit || 10;
      const c = document.getElementById('staff-activity-list');
      if (!c) return;
      try {
        const res = await apiRequest(`/api/admin/staff/activity?page=${page}&limit=${limit}`);
        const acts = res.data || [];
        if (acts.length === 0) {
          c.innerHTML = '<div style="text-align:center; padding:1rem; color:var(--admin-text-secondary); font-size:0.85rem;">No staff audit activity logged.</div>';
          renderPagination('staff-activity-pagination', 'audit', res.pagination);
          return;
        }
        c.innerHTML = acts.map(a => `
          <div style="display:flex; justify-content:space-between; align-items:center; padding:0.6rem 0.85rem; background:#F8FAFC; border-radius:6px; border:1px solid #E2E8F0; font-size:0.84rem;">
            <div>
              <strong style="color:var(--admin-primary);">${a.admin_username || 'Admin'}</strong>
              <span style="color:var(--admin-text-main); margin-left:6px;">${a.details || a.action}</span>
            </div>
            <span style="font-size:0.75rem; color:var(--admin-text-subtle);">${(a.created_at || '').substring(0, 16).replace('T', ' ')}</span>
          </div>
        `).join('');

        renderPagination('staff-activity-pagination', 'audit', res.pagination);
      } catch (e) {
        c.innerHTML = `<div style="color:red; font-size:0.8rem;">${e.message}</div>`;
      }
    }'''
    match = re.search(old_activity_pattern, content)
    if match:
        content = content[:match.start()] + new_activity_func + content[match.end():]
        print("Updated loadStaffActivity.")
    else:
        print("WARNING: Could not match old_activity_pattern")

    # 11. Update loadAdminMessages to call renderPagination
    content = content.replace("async function loadAdminMessages(page = 1) {", "async function loadAdminMessages(page = 1, limit = null) {\n      limit = limit || adminPages.messages.limit || 10;")
    content = content.replace("let url = `/api/admin/messages?page=${page}&limit=10`;", "let url = `/api/admin/messages?page=${page}&limit=${limit}`;")
    old_msg_end = '        tbody.innerHTML = msgs.map(m => `\n          <tr>\n            <td data-label="Sender"><strong>${m.name || \'Anonymous\'}</strong><br><span style="font-size:0.75rem; color:var(--admin-text-secondary);">${m.email || \'\'}</span></td>\n            <td data-label="Subject">${m.subject || \'Inquiry\'}</td>\n            <td data-label="Message Snippet"><span style="font-size:0.84rem; color:var(--admin-text-secondary);">${(m.message || \'\').substring(0, 50)}...</span></td>\n            <td data-label="Date"><span style="font-size:0.8rem; color:var(--admin-text-secondary);">${(m.created_at || \'\').substring(0, 10)}</span></td>\n            <td data-label="Status"><span class="badge-status ${m.status === \'replied\' ? \'badge-approved\' : \'badge-pending\'}">${m.status || \'new\'}</span></td>\n            <td data-label="Actions" style="text-align:right;">\n              <button class="btn-table-action danger" onclick="deleteContactMsg(${m.id})"><i class="fas fa-trash"></i></button>\n            </td>\n          </tr>\n        `).join(\'\');\n      } catch (err) {'
    new_msg_end = '        tbody.innerHTML = msgs.map(m => `\n          <tr>\n            <td data-label="Sender"><strong>${m.name || \'Anonymous\'}</strong><br><span style="font-size:0.75rem; color:var(--admin-text-secondary);">${m.email || \'\'}</span></td>\n            <td data-label="Subject">${m.subject || \'Inquiry\'}</td>\n            <td data-label="Message Snippet"><span style="font-size:0.84rem; color:var(--admin-text-secondary);">${(m.message || \'\').substring(0, 50)}...</span></td>\n            <td data-label="Date"><span style="font-size:0.8rem; color:var(--admin-text-secondary);">${(m.created_at || \'\').substring(0, 10)}</span></td>\n            <td data-label="Status"><span class="badge-status ${m.status === \'replied\' ? \'badge-approved\' : \'badge-pending\'}">${m.status || \'new\'}</span></td>\n            <td data-label="Actions" style="text-align:right;">\n              <button class="btn-table-action danger" onclick="deleteContactMsg(${m.id})"><i class="fas fa-trash"></i></button>\n            </td>\n          </tr>\n        `).join(\'\');\n\n        renderPagination(\'messages-pagination\', \'messages\', res.pagination);\n      } catch (err) {'
    if old_msg_end in content:
        content = content.replace(old_msg_end, new_msg_end, 1)
        print("Updated loadAdminMessages end.")
    else:
        old_msg_end_crlf = old_msg_end.replace('\n', '\r\n')
        new_msg_end_crlf = new_msg_end.replace('\n', '\r\n')
        if old_msg_end_crlf in content:
            content = content.replace(old_msg_end_crlf, new_msg_end_crlf, 1)
            print("Updated loadAdminMessages end (CRLF).")
        else:
            print("WARNING: Could not match old_msg_end")

    # 12. Update switchAdminTab to load current pages
    content = content.replace("else if (tabId === 'tab-bikes') loadAdminBikes(currentBikeTab, 1);", "else if (tabId === 'tab-bikes') loadAdminBikes(currentBikeTab, adminPages.bikes.page, adminPages.bikes.limit);")
    content = content.replace("else if (tabId === 'tab-soldout') loadSoldOutBikesView(1);", "else if (tabId === 'tab-soldout') loadSoldOutBikesView(adminPages.soldout.page, adminPages.soldout.limit);")
    content = content.replace("else if (tabId === 'tab-enquiries') loadAdminEnquiries('all', 1);", "else if (tabId === 'tab-enquiries') loadAdminEnquiries(currentEnquiryTab, adminPages.enquiries.page, adminPages.enquiries.limit);")
    content = content.replace("else if (tabId === 'tab-users') loadAdminUsers('all', 1);", "else if (tabId === 'tab-users') loadAdminUsers(currentUserTab, adminPages.users.page, adminPages.users.limit);")
    content = content.replace("else if (tabId === 'tab-staff') loadAdminStaff();", "else if (tabId === 'tab-staff') { loadAdminStaff(adminPages.staff.page, adminPages.staff.limit); loadStaffActivity(adminPages.audit.page, adminPages.audit.limit); }")
    content = content.replace("else if (tabId === 'tab-messages') loadAdminMessages(1);", "else if (tabId === 'tab-messages') loadAdminMessages(adminPages.messages.page, adminPages.messages.limit);")

    with open(ADMIN_HTML, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Saved admin.html.")

patch_admin()
