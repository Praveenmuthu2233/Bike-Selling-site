import os

def update_sold_bike_details():
    fpath = os.path.join("my-node-app", "templates", "sold-bike-details.html")
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Add ownership-docs-card-box right above or below proof-card-box
    proof_box_marker = '<!-- Identity Verification & Proof Card (Sold Units Only) -->'
    ownership_box = """<!-- Section C: Vehicle Ownership Documents (RC, Insurance, ID Proof) -->
          <div class="card-box" id="ownership-docs-card-box" style="display:none;">
            <div class="card-box-header">
              <h3 class="card-box-title"><i class="fas fa-file-shield" style="color:var(--info);"></i> Vehicle Ownership Documents</h3>
              <span id="ownership-doc-count" style="font-size:0.75rem; font-weight:800; padding:2px 8px; border-radius:4px; background:#EFF6FF; color:#1E40AF;">0 DOCS</span>
            </div>
            <div id="ownership-docs-list" style="display:flex; flex-direction:column; gap:8px;">
              <!-- Populated dynamically via JS -->
            </div>
          </div>

          <!-- Identity Verification & Proof Card (Sold Units Only) -->"""

    if proof_box_marker in content and 'ownership-docs-card-box' not in content:
        content = content.replace(proof_box_marker, ownership_box, 1)
        print("Added ownership-docs-card-box HTML")

    # 2. Update getAdminToken() to cover all keys
    old_token_fn = """    function getAdminToken() {
      return localStorage.getItem('smr_admin_token') || sessionStorage.getItem('smr_admin_token');
    }"""

    new_token_fn = """    function getAdminToken() {
      return localStorage.getItem('admin_token') || localStorage.getItem('adminToken') || 
             localStorage.getItem('smr_admin_token') || sessionStorage.getItem('admin_token') || 
             sessionStorage.getItem('adminToken') || sessionStorage.getItem('smr_admin_token');
    }"""

    if old_token_fn in content:
        content = content.replace(old_token_fn, new_token_fn, 1)
        print("Updated getAdminToken()")

    # 3. Update loadBikeFullDetails to support public visitors without redirect
    old_load_details = """    async function loadBikeFullDetails() {
      if (!bikeId) {
        showError('Missing Motorcycle ID', 'Please specify a valid motorcycle ID in the URL parameter (?id=X).');
        return;
      }

      const token = getAdminToken();
      if (!token) {
        window.location.href = '/adminLogin.html';
        return;
      }

      try {
        const res = await fetch(`/api/admin/sold-bikes/${bikeId}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });

        if (res.status === 401 || res.status === 403) {
          if (res.status === 401) {
            window.location.href = '/adminLogin.html';
            return;
          }
        }

        const data = await res.json();
        if (!res.ok || !data.success) {
          showError('Unable to Load Motorcycle', data.message || 'The requested motorcycle record is unavailable.');
          return;
        }

        currentBikeData = data.data;
        isSuperAdmin = !!data.is_superadmin;
        renderDetails(currentBikeData);

      } catch (err) {
        showError('Connection Error', err.message || 'Unable to communicate with the TiDB backend server.');
      }
    }"""

    new_load_details = """    async function loadBikeFullDetails() {
      if (!bikeId) {
        showError('Missing Motorcycle ID', 'Please specify a valid motorcycle ID in the URL parameter (?id=X).');
        return;
      }

      const token = getAdminToken();
      if (token) {
        try {
          const res = await fetch(`/api/admin/sold-bikes/${bikeId}`, {
            headers: { 'Authorization': `Bearer ${token}` }
          });

          if (res.ok) {
            const data = await res.json();
            if (data && data.success && data.data) {
              currentBikeData = data.data;
              isSuperAdmin = !!data.is_superadmin;
              renderDetails(currentBikeData, 'admin');
              return;
            }
          }
        } catch (adminErr) {
          console.warn('Admin fetch notice, falling back to public view:', adminErr);
        }
      }

      // Public visitor flow: never redirect to login
      try {
        const res = await fetch(`/api/bikes/${bikeId}`);
        const data = await res.json();
        if (res.ok && data) {
          const bike = data.data || data;
          currentBikeData = bike;
          isSuperAdmin = false;
          renderDetails(currentBikeData, 'public');
        } else {
          showError('Motorcycle Not Found', data.message || 'The requested motorcycle is not currently listed.');
        }
      } catch (err) {
        showError('Connection Error', err.message || 'Unable to communicate with the TiDB backend server.');
      }
    }"""

    if old_load_details in content:
        content = content.replace(old_load_details, new_load_details, 1)
        print("Updated loadBikeFullDetails() for role-based viewing")
    else:
        print("old_load_details target not matched")

    # 4. Enhance renderDetails for public vs admin vs superadmin
    old_render = """    function renderDetails(bike) {"""
    new_render = """    function renderDetails(bike, viewRole = 'admin') {"""
    if old_render in content:
        content = content.replace(old_render, new_render, 1)

    # In renderDetails, adjust backBtn and role visibility
    old_back_setup = """      // Top Back Button Text
      const backBtn = document.getElementById('btn-back');
      if (isSold) {
        backBtn.innerHTML = '<i class="fas fa-arrow-left"></i> Back to Sold Out Bikes';
      } else {
        backBtn.innerHTML = '<i class="fas fa-arrow-left"></i> Back to Bike Management';
      }"""

    new_back_setup = """      // Top Back Button & Role Handling
      const backBtn = document.getElementById('btn-back');
      const exportGroup = document.querySelector('.export-btn-group');
      if (viewRole === 'public') {
        backBtn.href = '/SoldOutPage.html';
        backBtn.innerHTML = '<i class="fas fa-arrow-left"></i> Back to Sold Gallery';
        if (exportGroup) exportGroup.style.display = 'none';
      } else {
        backBtn.href = '/admin.html';
        backBtn.innerHTML = isSold ? '<i class="fas fa-arrow-left"></i> Back to Sold Out Bikes' : '<i class="fas fa-arrow-left"></i> Back to Admin Dashboard';
        if (exportGroup) exportGroup.style.display = 'flex';
      }"""

    if old_back_setup in content:
        content = content.replace(old_back_setup, new_back_setup, 1)
        print("Updated backBtn setup in renderDetails")

    # In renderDetails, handle masked reg vs unmasked reg
    old_reg_setup = """      document.getElementById('hero-reg-no').textContent = bike.registration_number || 'TN-XX-XXXX';"""
    new_reg_setup = """      if (viewRole === 'public') {
        document.getElementById('hero-reg-no').textContent = bike.registration_number_masked || 'TN-**-****';
      } else {
        document.getElementById('hero-reg-no').textContent = bike.registration_number || 'TN-XX-XXXX';
      }"""

    if old_reg_setup in content:
        content = content.replace(old_reg_setup, new_reg_setup, 1)
        print("Updated hero-reg-no masking")

    old_spec_reg = """      document.getElementById('spec-reg').textContent = bike.registration_number || 'TN-XX-XXXX';"""
    new_spec_reg = """      if (viewRole === 'public') {
        document.getElementById('spec-reg').textContent = bike.registration_number_masked || 'TN-**-****';
      } else {
        document.getElementById('spec-reg').textContent = bike.registration_number || 'TN-XX-XXXX';
      }"""

    if old_spec_reg in content:
        content = content.replace(old_spec_reg, new_spec_reg, 1)
        print("Updated spec-reg masking")

    # Section B, C, D visibility based on viewRole
    old_fin_check = """      // Superadmin Financials
      const finBox = document.getElementById('financial-card-box');
      const editFinBtn = document.getElementById('btn-edit-financials');
      if (isSuperAdmin && bike.financials) {"""

    new_fin_check = """      // Section D: Superadmin Financials (Superadmin Only)
      const finBox = document.getElementById('financial-card-box');
      const editFinBtn = document.getElementById('btn-edit-financials');
      const enqBox = document.getElementById('enquiry-card-box');
      if (viewRole === 'admin' && isSuperAdmin && bike.financials) {"""

    if old_fin_check in content:
        content = content.replace(old_fin_check, new_fin_check, 1)
        print("Updated fin_check for Superadmin only")

    # Hide buyerBox for public
    old_buyer_check = """      // Buyer Info Section
      const buyerBox = document.getElementById('buyer-card-box');
      const buyerActiveDeal = document.getElementById('buyer-active-deal');
      const buyerNotSold = document.getElementById('buyer-not-sold-deal');

      if (isSold && bike.customer) {"""

    new_buyer_check = """      // Section B: Buyer Info Section (Admin/Superadmin Only)
      const buyerBox = document.getElementById('buyer-card-box');
      const buyerActiveDeal = document.getElementById('buyer-active-deal');
      const buyerNotSold = document.getElementById('buyer-not-sold-deal');

      if (viewRole === 'public') {
        if (buyerBox) buyerBox.style.display = 'none';
      } else if (isSold && bike.customer) {"""

    if old_buyer_check in content:
        content = content.replace(old_buyer_check, new_buyer_check, 1)
        print("Updated buyerBox for public")

    # Ownership documents rendering in Section C
    old_proof_check = """      // Identity Proof Document Card
      const proofCard = document.getElementById('proof-card-box');
      if (isSold && bike.proof_document) {"""

    new_proof_check = """      // Section C: Ownership Documents & Proof (Admin/Superadmin Only)
      const ownBox = document.getElementById('ownership-docs-card-box');
      const proofCard = document.getElementById('proof-card-box');

      if (viewRole === 'public') {
        if (ownBox) ownBox.style.display = 'none';
        if (proofCard) proofCard.style.display = 'none';
      } else {
        // Render bike_documents
        const bDocs = bike.bike_documents || [];
        if (ownBox) {
          if (bDocs.length > 0) {
            ownBox.style.display = 'block';
            document.getElementById('ownership-doc-count').textContent = `${bDocs.length} DOCS`;
            document.getElementById('ownership-docs-list').innerHTML = bDocs.map(d => {
              const typeLabel = {
                'rc_book': 'RC Book (Registration Certificate)',
                'insurance': 'Insurance Policy',
                'owner_id': 'Owner Identity Proof',
                'other': 'Other Vehicle Document'
              }[d.doc_type] || (d.doc_type || 'Document').toUpperCase();

              const stBadge = d.status === 'approved' ? '<span class="status-badge-hero approved" style="font-size:0.7rem; padding:2px 8px;">VERIFIED</span>' :
                             (d.status === 'rejected' ? '<span class="status-badge-hero sold" style="font-size:0.7rem; padding:2px 8px;">REJECTED</span>' :
                             '<span class="status-badge-hero pending" style="font-size:0.7rem; padding:2px 8px;">PENDING REVIEW</span>');

              const tokenParam = encodeURIComponent(getAdminToken() || '');
              return `
                <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:var(--radius-sm); padding:0.75rem 1rem; display:flex; justify-content:space-between; align-items:center; gap:10px;">
                  <div>
                    <div style="font-size:0.85rem; font-weight:800; color:var(--text-main);">${typeLabel}</div>
                    <div style="font-size:0.75rem; color:var(--text-muted);">${d.file_name} • Uploaded ${d.created_at.substring(0, 10)}</div>
                    ${d.remarks ? `<div style="font-size:0.75rem; color:#DC2626; margin-top:2px;">Remark: ${d.remarks}</div>` : ''}
                  </div>
                  <div style="display:flex; align-items:center; gap:8px;">
                    ${stBadge}
                    <a href="${d.download_url}?token=${tokenParam}" target="_blank" class="back-btn" style="padding:0.35rem 0.65rem; font-size:0.75rem; background:var(--info); color:#FFFFFF; border-color:var(--info);">
                      <i class="fas fa-download"></i> View
                    </a>
                  </div>
                </div>
              `;
            }).join('');
          } else {
            ownBox.style.display = 'none';
          }
        }
      }

      if (viewRole !== 'public' && isSold && bike.proof_document) {"""

    if old_proof_check in content:
        content = content.replace(old_proof_check, new_proof_check, 1)
        print("Updated Section C proof and ownership documents")

    # Hide sale-payment-card-box for public
    old_sale_card = """      // Sale & Payment Card
      const saleCard = document.getElementById('sale-payment-card-box');
      if (isSold && bike.sale_info) {"""

    new_sale_card = """      // Sale & Payment Card (Staff Admin / Superadmin)
      const saleCard = document.getElementById('sale-payment-card-box');
      if (viewRole === 'public') {
        if (saleCard) saleCard.style.display = 'none';
      } else if (isSold && bike.sale_info) {"""

    if old_sale_card in content:
        content = content.replace(old_sale_card, new_sale_card, 1)
        print("Updated saleCard check for public")

    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
    print("sold-bike-details.html updated successfully")

if __name__ == "__main__":
    update_sold_bike_details()
