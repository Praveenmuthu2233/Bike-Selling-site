import os

def revert_public_soldout_page():
    fpath = os.path.join("my-node-app", "templates", "SoldOutPage.html")
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    # Restore main tag style
    content = content.replace(
        '<main class="main-content" style="padding: 3.5rem 0 5rem; background-color: #F8FAFC;">',
        '<main class="main-content" style="padding: 4.5rem 0 6rem;">'
    )

    # Restore limit to 8
    content = content.replace("const soldLimit = 6;", "const soldLimit = 8;")

    # Restore Details button
    content = content.replace(
        '<a href="/sold-bike-details.html?id=${bike.id}" class="btn btn-sm btn-primary" style="display:inline-flex; align-items:center; gap:6px; font-weight:700;"><i class="fas fa-eye"></i> View Details</a>',
        '<a href="/enquiry-bike-details.html?id=${bike.id}" class="btn btn-sm btn-outline">Details</a>'
    )

    # Completely remove any isSuper telemetry from public SoldOutPage
    old_telemetry = """                ${isSuper ? `
                  <!-- Superadmin Confidential Financial Telemetry -->
                  <div style="background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 6px; padding: 8px 10px; margin: 0.5rem 0; font-size: 0.78rem;">
                    <div style="font-weight: 700; color: #1D4ED8; margin-bottom: 3px; display:flex; justify-content:space-between;">
                      <span>SUPERADMIN TELEMETRY</span>
                      <span style="color:#16A34A;">Profit: ₹${Number(bike.realized_profit || 0).toLocaleString('en-IN')}</span>
                    </div>
                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 4px; color: var(--text-secondary);">
                      <div>Sale: ₹${Number(bike.actual_sale_price || bike.price || 0).toLocaleString('en-IN')}</div>
                      <div>Payout: ₹${Number(bike.seller_payout || 0).toLocaleString('en-IN')}</div>
                      <div>Expenses: ₹${Number(bike.total_expenses || 0).toLocaleString('en-IN')}</div>
                      <div>Sold By: ${bike.sold_by || 'Admin'}</div>
                    </div>
                  </div>
                ` : ''}"""
    if old_telemetry in content:
        content = content.replace(old_telemetry, '')

    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
    print("SoldOutPage.html successfully reverted to original public design and behavior.")

if __name__ == "__main__":
    revert_public_soldout_page()
