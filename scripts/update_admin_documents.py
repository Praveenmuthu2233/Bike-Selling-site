import os

def update_admin_html():
    fpath = os.path.join("my-node-app", "templates", "admin.html")
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Add "Docs" button to table actions
    old_actions = """                  <a href="/admin/sold-bike-details.html?id=${b.id}" class="btn-table-action" title="View Full Details & Financials"><i class="fas fa-eye"></i> View</a>
                  <button class="btn-table-action" onclick="openEditBikeModal(${b.id})" title="Edit Details"><i class="fas fa-edit"></i> Edit</button>"""

    new_actions = """                  <a href="/admin/sold-bike-details.html?id=${b.id}" class="btn-table-action" title="View Full Details & Financials"><i class="fas fa-eye"></i> View</a>
                  <button class="btn-table-action" onclick="openAdminBikeDocsModal(${b.id}, '${(b.title || (b.brand + ' ' + b.model)).replace(/'/g, "\\\\'")}')" title="Verify Ownership Documents"><i class="fas fa-file-shield"></i> Docs</button>
                  <button class="btn-table-action" onclick="openEditBikeModal(${b.id})" title="Edit Details"><i class="fas fa-edit"></i> Edit</button>"""

    if old_actions in content:
        content = content.replace(old_actions, new_actions, 1)
        print("Added Docs button in admin bike table")
    else:
        print("old_actions target not found in admin.html")

    # 2. Add Modal HTML before </body>
    modal_html = """
  <!-- Admin Bike Documents Verification Modal -->
  <div id="modal-admin-bike-docs" class="modal-overlay" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(15,23,42,0.6); z-index:9999; align-items:center; justify-content:center; padding:1rem; backdrop-filter:blur(3px);">
    <div style="background:#FFFFFF; border-radius:14px; max-width:760px; width:100%; max-height:90vh; overflow-y:auto; box-shadow:0 20px 25px -5px rgba(0,0,0,0.1), 0 10px 10px -5px rgba(0,0,0,0.04); border:1px solid #E2E8F0;">
      <div style="padding:1.25rem 1.5rem; border-bottom:1px solid #E2E8F0; display:flex; justify-content:space-between; align-items:center;">
        <div>
          <h3 style="font-size:1.15rem; font-weight:800; color:#0F172A; margin:0;" id="admin-docs-modal-title">Ownership Documents Verification</h3>
          <p style="font-size:0.8rem; color:#64748B; margin:3px 0 0;">Review seller RC book, insurance, and ID proofs. Verified status updates customer account immediately.</p>
        </div>
        <button type="button" onclick="closeAdminBikeDocsModal()" style="background:none; border:none; font-size:1.4rem; color:#94A3B8; cursor:pointer; padding:4px 8px;">&times;</button>
      </div>

      <div style="padding:1.5rem;">
        <div id="admin-docs-table-container">
          <div style="text-align:center; padding:2rem; color:#64748B;"><i class="fas fa-spinner fa-spin"></i> Fetching bike documents...</div>
        </div>
      </div>
      
      <div style="padding:1rem 1.5rem; background:#F8FAFC; border-top:1px solid #E2E8F0; text-align:right;">
        <button type="button" onclick="closeAdminBikeDocsModal()" class="btn-table-action" style="font-weight:700;">Close</button>
      </div>
    </div>
  </div>
"""

    if 'modal-admin-bike-docs' not in content:
        content = content.replace('</body>', modal_html + '\n</body>')
        print("Added modal-admin-bike-docs to admin.html")

    # 3. Add JS functions
    js_code = """
  // Admin Bike Documents Verification
  let currentAdminDocBikeId = null;

  async function openAdminBikeDocsModal(bikeId, bikeTitle) {
    currentAdminDocBikeId = bikeId;
    document.getElementById('admin-docs-modal-title').textContent = `${bikeTitle} – Documents Verification`;
    const modal = document.getElementById('modal-admin-bike-docs');
    if (modal) modal.style.display = 'flex';
    loadAdminBikeDocs(bikeId);
  }

  function closeAdminBikeDocsModal() {
    const modal = document.getElementById('modal-admin-bike-docs');
    if (modal) modal.style.display = 'none';
    currentAdminDocBikeId = null;
  }

  async function loadAdminBikeDocs(bikeId) {
    const container = document.getElementById('admin-docs-table-container');
    container.innerHTML = '<div style="text-align:center; padding:2rem; color:#64748B;"><i class="fas fa-spinner fa-spin"></i> Fetching documents...</div>';
    try {
      const token = localStorage.getItem('admin_token') || localStorage.getItem('adminToken') || localStorage.getItem('smr_admin_token') || sessionStorage.getItem('admin_token') || sessionStorage.getItem('adminToken');
      const res = await fetch(`/api/admin/bikes/${bikeId}/documents`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      });
      const data = await res.json();
      const docs = data.data || [];

      if (!docs || docs.length === 0) {
        container.innerHTML = '<div style="text-align:center; padding:2rem; color:#64748B; background:#F8FAFC; border-radius:8px; border:1px dashed #CBD5E1;"><i class="fas fa-file-circle-question" style="font-size:2rem; margin-bottom:0.5rem; display:block; color:#94A3B8;"></i>No ownership documents have been uploaded for this motorcycle yet.</div>';
        return;
      }

      const typeLabels = {
        'rc_book': 'RC Book (Registration Certificate)',
        'insurance': 'Insurance Policy',
        'owner_id': 'Owner Identity Proof',
        'other': 'Other Vehicle Document'
      };

      const tokenParam = encodeURIComponent(token || '');

      container.innerHTML = `
        <div style="overflow-x:auto;">
          <table style="width:100%; border-collapse:collapse; font-size:0.85rem;">
            <thead>
              <tr style="border-bottom:2px solid #E2E8F0; color:#64748B; text-align:left;">
                <th style="padding:10px;">Document Type</th>
                <th style="padding:10px;">File Name</th>
                <th style="padding:10px;">Uploaded</th>
                <th style="padding:10px;">Current Status</th>
                <th style="padding:10px; text-align:right;">Actions</th>
              </tr>
            </thead>
            <tbody>
              ${docs.map(d => {
                const stBadge = d.status === 'approved' ? '<span class="badge-status badge-approved" style="font-size:0.75rem;"><i class="fas fa-check-circle"></i> Verified</span>' :
                               (d.status === 'rejected' ? '<span class="badge-status badge-rejected" style="font-size:0.75rem;"><i class="fas fa-xmark"></i> Rejected</span>' :
                               '<span class="badge-status badge-pending" style="font-size:0.75rem;"><i class="fas fa-clock"></i> Pending</span>');
                return `
                  <tr style="border-bottom:1px solid #F1F5F9;">
                    <td style="padding:10px; font-weight:700; color:#0F172A;">${typeLabels[d.doc_type] || d.doc_type}</td>
                    <td style="padding:10px; color:#475569; max-width:180px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${d.file_name}</td>
                    <td style="padding:10px; color:#64748B;">${(d.created_at || '').substring(0, 10)}</td>
                    <td style="padding:10px;">
                      ${stBadge}
                      ${d.remarks ? `<div style="font-size:0.75rem; color:#DC2626; margin-top:2px;">${d.remarks}</div>` : ''}
                    </td>
                    <td style="padding:10px; text-align:right;">
                      <div style="display:inline-flex; gap:6px; align-items:center;">
                        <a href="${d.download_url}?token=${tokenParam}" target="_blank" class="btn-table-action" title="View Document File"><i class="fas fa-eye"></i> View</a>
                        <button onclick="verifyDocAction(${bikeId}, ${d.id}, 'approved')" class="btn-table-action success" title="Approve & Verify"><i class="fas fa-check"></i></button>
                        <button onclick="verifyDocAction(${bikeId}, ${d.id}, 'rejected')" class="btn-table-action danger" title="Reject with Reason"><i class="fas fa-xmark"></i></button>
                      </div>
                    </td>
                  </tr>
                `;
              }).join('')}
            </tbody>
          </table>
        </div>
      `;
    } catch (err) {
      container.innerHTML = `<div style="text-align:center; padding:2rem; color:#DC2626;">${err.message || 'Error fetching documents'}</div>`;
    }
  }

  async function verifyDocAction(bikeId, docId, status) {
    let remarks = 'Verified and approved by SMR Motors Administrator';
    if (status === 'rejected') {
      const reason = prompt('Please enter the reason for rejecting this document (e.g. Unclear photo, Expired policy):');
      if (reason === null) return;
      remarks = reason.trim() || 'Document does not meet verification requirements';
    }

    try {
      const token = localStorage.getItem('admin_token') || localStorage.getItem('adminToken') || localStorage.getItem('smr_admin_token') || sessionStorage.getItem('admin_token') || sessionStorage.getItem('adminToken');
      const res = await fetch(`/api/admin/bikes/${bikeId}/documents/${docId}/verify`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify({ status: status, remarks: remarks })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        showToast(data.message || `Document marked as ${status}`, 'success');
        loadAdminBikeDocs(bikeId);
      } else {
        showToast(data.message || 'Verification update failed', 'error');
      }
    } catch (err) {
      showToast(err.message || 'Connection error', 'error');
    }
  }
"""

    if 'function openAdminBikeDocsModal' not in content:
        content = content.replace('</script>', js_code + '\n</script>')
        print("Added JS functions to admin.html")

    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
    print("admin.html updated successfully")

if __name__ == "__main__":
    update_admin_html()
