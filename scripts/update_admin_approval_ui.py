import os

def update_admin():
    admin_path = os.path.join("my-node-app", "templates", "admin.html")
    with open(admin_path, "r", encoding="utf-8") as f:
        content = f.read()

    content = content.replace('\r\n', '\n')

    # Add pendingApprovalsList declaration near adminBikesList
    old_var_decl = "let adminBikesList = [];"
    new_var_decl = "let adminBikesList = [];\n    let pendingApprovalsList = [];"
    if old_var_decl in content and "let pendingApprovalsList" not in content:
        content = content.replace(old_var_decl, new_var_decl, 1)
        print("Added pendingApprovalsList declaration")

    # Store pending into pendingApprovalsList in loadPendingApprovals()
    old_store = "const pending = res.data || [];"
    new_store = "const pending = res.data || [];\n        pendingApprovalsList = pending;"
    if old_store in content and "pendingApprovalsList = pending;" not in content:
        content = content.replace(old_store, new_store, 1)
        print("Updated loadPendingApprovals to store pendingApprovalsList")

    # Update openApproveBikeModal function
    old_modal_start = "function openApproveBikeModal(id, title = '', currentPrice = '') {"
    new_modal_fn = """function openApproveBikeModal(id, title = '', currentPrice = '') {
      document.getElementById('approve-bike-id').value = id;
      document.getElementById('approve-bike-title-text').textContent = title ? `"${title}"` : `#${id}`;
      
      const priceGroup = document.getElementById('approve-price-group');
      if (priceGroup) priceGroup.style.display = 'block';

      const priceInput = document.getElementById('approve-bike-price');
      if (priceInput) {
        let p = currentPrice;
        if (p === '' || p === undefined || p === null) {
          if (typeof pendingApprovalsList !== 'undefined' && Array.isArray(pendingApprovalsList)) {
            const found = pendingApprovalsList.find(b => b.id == id);
            if (found && (found.requested_price || found.price)) p = found.requested_price || found.price;
          }
          if (!p && typeof adminBikesList !== 'undefined' && Array.isArray(adminBikesList)) {
            const found = adminBikesList.find(b => b.id == id);
            if (found && found.price) p = found.price;
          }
        }
        priceInput.value = (p !== undefined && p !== null && p !== '') ? parseFloat(p) : '';
      }

      openModal('modal-approve-bike');
    }"""

    # Replace the existing openApproveBikeModal implementation
    fn_idx = content.find(old_modal_start)
    if fn_idx != -1:
        close_idx = content.find("async function confirmApproveBike()", fn_idx)
        if close_idx != -1:
            content = content[:fn_idx] + new_modal_fn + "\n\n    " + content[close_idx:]
            print("Refined openApproveBikeModal")

    # Update button onclick in line 3500 (pending cards)
    old_btn = '<button class="btn-review-approve" onclick="openApproveBikeModal(${b.id}, \'${b.title.replace(/\'/g, "\\\\\'")}\')">'
    new_btn = '<button class="btn-review-approve" onclick="openApproveBikeModal(${b.id}, \'${b.title.replace(/\'/g, "\\\\\'")}\', ${b.requested_price || b.price || 0})">'
    if old_btn in content:
        content = content.replace(old_btn, new_btn, 1)
        print("Updated pending card approve button onclick")

    with open(admin_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("admin.html updated successfully")

if __name__ == "__main__":
    update_admin()
