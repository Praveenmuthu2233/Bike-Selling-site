import os

def update_profile_docs(fpath):
    if not os.path.exists(fpath):
        print(f"File {fpath} does not exist, skipping.")
        return

    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Add "Docs" button to listings table
    old_actions = """                  ${st === 'approved' || st === 'published' ? `
                    <a href="/enquiry-bike-details.html?id=${bike.id}" class="btn btn-sm btn-outline" target="_blank" title="View Showroom Listing"><i class="fas fa-eye"></i></a>
                  ` : ''}
                  <button onclick="deleteMyBike(${bike.id})" class="btn btn-sm btn-danger" title="Delete Listing"><i class="fas fa-trash"></i></button>"""

    new_actions = """                  <button onclick="openUserBikeDocsModal(${bike.id}, '${(bike.brand + ' ' + bike.model).replace(/'/g, "\\\\'")}')" class="btn btn-sm btn-outline" style="border-color:#2563EB; color:#2563EB;" title="Upload & View Ownership Documents"><i class="fas fa-file-shield"></i> Docs</button>
                  ${st === 'approved' || st === 'published' ? `
                    <a href="/enquiry-bike-details.html?id=${bike.id}" class="btn btn-sm btn-outline" target="_blank" title="View Showroom Listing"><i class="fas fa-eye"></i></a>
                  ` : ''}
                  <button onclick="deleteMyBike(${bike.id})" class="btn btn-sm btn-danger" title="Delete Listing"><i class="fas fa-trash"></i></button>"""

    if old_actions in content:
        content = content.replace(old_actions, new_actions)
        print(f"Added Docs button in {fpath}")
    else:
        print(f"Old actions target not found in {fpath}")

    # 2. Add Modal HTML before </body>
    modal_html = """
  <!-- Customer Ownership Documents Modal -->
  <div id="modal-user-bike-docs" class="modal-overlay" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(15,23,42,0.6); z-index:9999; align-items:center; justify-content:center; padding:1rem; backdrop-filter:blur(3px);">
    <div style="background:#FFFFFF; border-radius:14px; max-width:680px; width:100%; max-height:90vh; overflow-y:auto; box-shadow:0 20px 25px -5px rgba(0,0,0,0.1), 0 10px 10px -5px rgba(0,0,0,0.04); border:1px solid #E2E8F0;">
      <div style="padding:1.25rem 1.5rem; border-bottom:1px solid #E2E8F0; display:flex; justify-content:space-between; align-items:center;">
        <div>
          <h3 style="font-size:1.15rem; font-weight:800; color:#0F172A; margin:0;" id="user-docs-modal-title">Bike Ownership Documents</h3>
          <p style="font-size:0.8rem; color:#64748B; margin:3px 0 0;">Upload required vehicle documents to complete your selling verification.</p>
        </div>
        <button type="button" onclick="closeUserBikeDocsModal()" style="background:none; border:none; font-size:1.4rem; color:#94A3B8; cursor:pointer; padding:4px 8px;">&times;</button>
      </div>

      <div style="padding:1.5rem;">
        <!-- Required Documents Notice -->
        <div style="background:#EFF6FF; border:1px solid #BFDBFE; border-radius:8px; padding:0.85rem 1rem; margin-bottom:1.5rem; font-size:0.82rem; color:#1E40AF;">
          <div style="font-weight:700; margin-bottom:4px;"><i class="fas fa-info-circle"></i> Required Documents for Verification:</div>
          <ul style="margin:0; padding-left:1.2rem; line-height:1.5;">
            <li><strong>RC Book:</strong> Registration certificate showing active validity</li>
            <li><strong>Insurance:</strong> Valid two-wheeler insurance policy</li>
            <li><strong>Owner Identity Proof:</strong> Aadhaar Card, Driving License, or PAN Card</li>
            <li><strong>Other Documents:</strong> NOC, PUC, or Service book if available</li>
          </ul>
        </div>

        <!-- Upload Form -->
        <form id="user-doc-upload-form" onsubmit="handleUserDocUpload(event)" style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:10px; padding:1.25rem; margin-bottom:1.5rem;">
          <input type="hidden" id="user-doc-bike-id" value="">
          <div style="display:grid; grid-template-columns:1fr 1fr; gap:1rem; margin-bottom:1rem;">
            <div>
              <label style="display:block; font-size:0.8rem; font-weight:700; color:#0F172A; margin-bottom:4px;">Document Type *</label>
              <select id="user-doc-type" class="form-control" style="width:100%; padding:0.5rem 0.75rem; border:1px solid #CBD5E1; border-radius:6px; font-size:0.88rem;" required>
                <option value="rc_book">RC Book (Registration Certificate)</option>
                <option value="insurance">Insurance Policy</option>
                <option value="owner_id">Owner Identity Proof (Aadhaar/DL/PAN)</option>
                <option value="other">Other Vehicle Document</option>
              </select>
            </div>
            <div>
              <label style="display:block; font-size:0.8rem; font-weight:700; color:#0F172A; margin-bottom:4px;">Choose File (PDF/Image <= 10MB) *</label>
              <input type="file" id="user-doc-file" class="form-control" accept=".pdf,.jpg,.jpeg,.png,.webp" style="width:100%; padding:0.45rem 0.75rem; border:1px solid #CBD5E1; border-radius:6px; font-size:0.85rem;" required>
            </div>
          </div>
          <button type="submit" id="btn-upload-doc" class="btn btn-primary" style="width:100%; display:flex; align-items:center; justify-content:center; gap:0.5rem; font-weight:700;">
            <i class="fas fa-cloud-arrow-up"></i> Upload Document for Verification
          </button>
        </form>

        <!-- Uploaded Documents Table -->
        <h4 style="font-size:0.95rem; font-weight:800; color:#0F172A; margin-bottom:0.75rem;"><i class="fas fa-list-check"></i> Uploaded Documents</h4>
        <div id="user-docs-table-container">
          <div style="text-align:center; padding:1.5rem; color:#64748B;"><i class="fas fa-spinner fa-spin"></i> Loading uploaded documents...</div>
        </div>
      </div>
      
      <div style="padding:1rem 1.5rem; background:#F8FAFC; border-top:1px solid #E2E8F0; text-align:right;">
        <button type="button" onclick="closeUserBikeDocsModal()" class="btn btn-outline" style="font-weight:700;">Close</button>
      </div>
    </div>
  </div>
"""

    if 'modal-user-bike-docs' not in content:
        content = content.replace('</body>', modal_html + '\n</body>')
        print(f"Added modal-user-bike-docs to {fpath}")

    # 3. Add JS functions
    js_code = """
    // User Bike Documents Management
    let currentDocBikeId = null;

    function openUserBikeDocsModal(bikeId, bikeTitle) {
      currentDocBikeId = bikeId;
      document.getElementById('user-doc-bike-id').value = bikeId;
      document.getElementById('user-docs-modal-title').textContent = `${bikeTitle} – Documents`;
      const modal = document.getElementById('modal-user-bike-docs');
      if (modal) modal.style.display = 'flex';
      loadUserBikeDocs(bikeId);
    }

    function closeUserBikeDocsModal() {
      const modal = document.getElementById('modal-user-bike-docs');
      if (modal) modal.style.display = 'none';
      currentDocBikeId = null;
    }

    async function loadUserBikeDocs(bikeId) {
      const container = document.getElementById('user-docs-table-container');
      container.innerHTML = '<div style="text-align:center; padding:1.5rem; color:#64748B;"><i class="fas fa-spinner fa-spin"></i> Loading documents...</div>';
      try {
        const res = await apiRequest(`/api/users/bikes/${bikeId}/documents`);
        const docs = res.data || [];
        if (docs.length === 0) {
          container.innerHTML = '<div style="text-align:center; padding:1.5rem; color:#64748B; background:#F8FAFC; border-radius:8px; border:1px dashed #CBD5E1;">No documents uploaded yet. Upload your RC book or insurance above.</div>';
          return;
        }

        const typeLabels = {
          'rc_book': 'RC Book',
          'insurance': 'Insurance Policy',
          'owner_id': 'Owner Identity Proof',
          'other': 'Other Vehicle Doc'
        };

        const statusBadges = {
          'pending': '<span class="badge badge-pending" style="font-size:0.75rem;"><i class="fas fa-clock"></i> Pending Review</span>',
          'approved': '<span class="badge badge-approved" style="font-size:0.75rem;"><i class="fas fa-check-circle"></i> Verified</span>',
          'rejected': '<span class="badge badge-rejected" style="font-size:0.75rem;"><i class="fas fa-circle-xmark"></i> Rejected</span>'
        };

        const token = localStorage.getItem('token') || sessionStorage.getItem('token');
        const tokenParam = token ? `?token=${encodeURIComponent(token)}` : '';

        container.innerHTML = `
          <div style="overflow-x:auto;">
            <table style="width:100%; border-collapse:collapse; font-size:0.85rem;">
              <thead>
                <tr style="border-bottom:1px solid #CBD5E1; color:#64748B; text-align:left;">
                  <th style="padding:8px 10px;">Type</th>
                  <th style="padding:8px 10px;">File</th>
                  <th style="padding:8px 10px;">Uploaded</th>
                  <th style="padding:8px 10px;">Status</th>
                  <th style="padding:8px 10px; text-align:right;">Action</th>
                </tr>
              </thead>
              <tbody>
                ${docs.map(d => `
                  <tr style="border-bottom:1px solid #F1F5F9;">
                    <td style="padding:10px; font-weight:700; color:#0F172A;">${typeLabels[d.doc_type] || d.doc_type}</td>
                    <td style="padding:10px; color:#475569; max-width:160px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${d.file_name}</td>
                    <td style="padding:10px; color:#64748B;">${(d.created_at || '').substring(0, 10)}</td>
                    <td style="padding:10px;">
                      ${statusBadges[d.status] || d.status}
                      ${d.remarks ? `<div style="font-size:0.75rem; color:#DC2626; margin-top:2px;"><strong>Remark:</strong> ${d.remarks}</div>` : ''}
                    </td>
                    <td style="padding:10px; text-align:right;">
                      <a href="${d.download_url}${tokenParam}" target="_blank" class="btn btn-sm btn-outline" style="padding:3px 8px; font-size:0.75rem;"><i class="fas fa-eye"></i> View</a>
                    </td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        `;
      } catch (err) {
        container.innerHTML = `<div style="text-align:center; padding:1.5rem; color:#DC2626;">${err.message || 'Unable to load documents'}</div>`;
      }
    }

    async function handleUserDocUpload(e) {
      e.preventDefault();
      if (!currentDocBikeId) return;
      const fileInput = document.getElementById('user-doc-file');
      const docType = document.getElementById('user-doc-type').value;
      if (!fileInput.files || !fileInput.files[0]) {
        showToast('Please select a document file to upload', 'warning');
        return;
      }

      const file = fileInput.files[0];
      if (file.size > 10 * 1024 * 1024) {
        showToast('File size exceeds the 10MB limit', 'warning');
        return;
      }

      const btn = document.getElementById('btn-upload-doc');
      btn.disabled = true;
      btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Uploading Securely...';

      const formData = new FormData();
      formData.append('file', file);
      formData.append('doc_type', docType);

      try {
        const token = localStorage.getItem('token') || sessionStorage.getItem('token');
        const res = await fetch(`/api/users/bikes/${currentDocBikeId}/documents`, {
          method: 'POST',
          headers: token ? { 'Authorization': `Bearer ${token}` } : {},
          body: formData
        });

        const data = await res.json();
        if (res.ok && data.success) {
          showToast(data.message || 'Document uploaded successfully! Our team will review it.', 'success');
          fileInput.value = '';
          loadUserBikeDocs(currentDocBikeId);
        } else {
          showToast(data.message || 'Failed to upload document', 'error');
        }
      } catch (err) {
        showToast(err.message || 'Connection error during upload', 'error');
      } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-cloud-arrow-up"></i> Upload Document for Verification';
      }
    }
"""

    if 'function openUserBikeDocsModal' not in content:
        content = content.replace('</script>', js_code + '\n</script>')
        print(f"Added JS functions to {fpath}")

    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"{fpath} updated successfully")

if __name__ == "__main__":
    update_profile_docs(os.path.join("my-node-app", "templates", "profile.html"))
    update_profile_docs(os.path.join("user", "profile.html"))
