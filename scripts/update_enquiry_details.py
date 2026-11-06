import os

def update_enquiry_bike_details():
    fpath = os.path.join("my-node-app", "templates", "enquiry-bike-details.html")
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    # Look for the user check in loadBikeDetails
    old_code = """        const user = AuthService.getUser();
        if (user && !isSold) {
          const nameInp = document.getElementById('direct-name');
          if (nameInp) nameInp.value = user.name || '';
          const emailInp = document.getElementById('direct-email');
          if (emailInp) emailInp.value = user.email || '';
          const phoneInp = document.getElementById('direct-phone');
          if (phoneInp && user.phone) phoneInp.value = user.phone;
        }"""

    new_code = """        const user = AuthService.getUser();
        if (user && !isSold) {
          const actionContainer = document.getElementById('enquiry-action-container');
          if (actionContainer) {
            actionContainer.innerHTML = `
              <h3 style="font-size: 1.15rem; margin-bottom: 0.75rem; color:#0F172A; font-weight:700;">Interested in this Motorcycle?</h3>
              <p style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 1.25rem;">
                Schedule a test ride or express buying interest with 1-click using your verified account details.
              </p>

              <div style="background: rgba(37, 99, 235, 0.05); border: 1px solid rgba(37, 99, 235, 0.2); border-radius: var(--radius-md); padding: 1.25rem; margin-bottom: 1.25rem;">
                <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.75rem;">
                  <div style="width: 40px; height: 40px; border-radius: 50%; background: #2563EB; color: white; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 1.1rem;">
                    ${(user.name || 'U').charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <div style="font-weight: 700; color: #0F172A;">${user.name || 'Verified User'}</div>
                    <div style="font-size: 0.82rem; color: var(--text-secondary);">${user.email || ''} ${user.phone ? '• ' + user.phone : ''}</div>
                  </div>
                </div>
                <button id="btn-instant-enquiry" type="button" onclick="submitInstantEnquiry()" class="btn btn-lg btn-primary" style="width: 100%; display: flex; align-items: center; justify-content: center; gap: 0.5rem; font-weight: 700;">
                  <i class="fas fa-bolt"></i> Instant 1-Click Enquiry
                </button>
              </div>

              <div style="margin-top: 1rem; display: flex; flex-direction: column; gap: 0.75rem;">
                <button type="button" onclick="startDirectBikeChat()" class="btn btn-lg btn-outline" style="width: 100%; border-color: #ea580c; color: #ea580c; display: flex; align-items: center; justify-content: center; gap: 0.5rem; font-weight: 700;">
                  <i class="fab fa-whatsapp" style="font-size: 1.2rem; color: #25D366;"></i> Chat with SMR Support
                </button>
                <a href="tel:+917845215164" class="btn btn-secondary" style="width: 100%; display: flex; align-items: center; justify-content: center; gap: 0.5rem;"><i class="fas fa-phone"></i> Call Showroom</a>
              </div>
            `;
          }
        }"""

    if old_code in content:
        content = content.replace(old_code, new_code, 1)
        print("Updated user check in loadBikeDetails")
    else:
        print("user check target not found in enquiry-bike-details.html")

    # Add submitInstantEnquiry and improve handleDirectBikeEnquiry
    old_enq_func = """    async function handleDirectBikeEnquiry(e) {
      e.preventDefault();
      if (!currentBike) return;
      const form = e.target;
      const submitBtn = form.querySelector('button[type="submit"]');
      submitBtn.disabled = true;

      const formData = new FormData(form);
      const payload = {
        bike_id: currentBike.id,
        name: formData.get('name'),
        email: formData.get('email'),
        phone: formData.get('phone'),
        message: formData.get('message')
      };

      try {
        const res = await apiRequest('/api/enquiries', { method: 'POST', body: payload });
        showToast(res.message || 'Enquiry submitted!', 'success');
        form.reset();
      } catch (err) {
        showToast(err.message || 'Failed to submit enquiry', 'error');
      } finally {
        submitBtn.disabled = false;
      }
    }"""

    new_enq_func = """    let instantEnquirySubmitting = false;
    async function submitInstantEnquiry() {
      if (instantEnquirySubmitting) return;
      if (!currentBike) return;
      const user = AuthService.getUser();
      if (!user) {
        showToast('Please sign in to submit an enquiry', 'info');
        return;
      }

      const btn = document.getElementById('btn-instant-enquiry');
      if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Submitting Enquiry...';
      }
      instantEnquirySubmitting = true;

      const payload = {
        bike_id: currentBike.id,
        user_id: user.id,
        name: user.name || '',
        email: user.email || '',
        phone: user.phone || '',
        message: `Direct interest in ${currentBike.year || ''} ${currentBike.title || currentBike.listingTitle || 'Motorcycle'}`
      };

      try {
        const res = await apiRequest('/api/enquiries', { method: 'POST', body: payload });
        showToast(res.message || 'Enquiry submitted successfully! Our team will contact you shortly.', 'success');
        if (btn) {
          btn.innerHTML = '<i class="fas fa-check-circle"></i> Enquiry Submitted!';
          btn.style.background = '#16A34A';
          btn.style.borderColor = '#16A34A';
          btn.disabled = true;
        }
      } catch (err) {
        showToast(err.message || 'Failed to submit enquiry', 'error');
        if (btn) {
          btn.disabled = false;
          btn.innerHTML = '<i class="fas fa-bolt"></i> Instant 1-Click Enquiry';
        }
      } finally {
        instantEnquirySubmitting = false;
      }
    }

    async function handleDirectBikeEnquiry(e) {
      e.preventDefault();
      if (!currentBike) return;
      const form = e.target;
      const submitBtn = form.querySelector('button[type="submit"]');
      submitBtn.disabled = true;

      const formData = new FormData(form);
      const payload = {
        bike_id: currentBike.id,
        name: formData.get('name'),
        email: formData.get('email'),
        phone: formData.get('phone'),
        message: formData.get('message')
      };

      try {
        const res = await apiRequest('/api/enquiries', { method: 'POST', body: payload });
        showToast(res.message || 'Enquiry submitted successfully! Our team will contact you shortly.', 'success');
        form.reset();
        submitBtn.innerHTML = '<i class="fas fa-check-circle"></i> Enquiry Submitted!';
        submitBtn.style.background = '#16A34A';
      } catch (err) {
        showToast(err.message || 'Failed to submit enquiry', 'error');
        submitBtn.disabled = false;
      }
    }"""

    if old_enq_func in content:
        content = content.replace(old_enq_func, new_enq_func, 1)
        print("Updated handleDirectBikeEnquiry and added submitInstantEnquiry")
    else:
        print("handleDirectBikeEnquiry target not found")

    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
    print("enquiry-bike-details.html updated successfully")

if __name__ == "__main__":
    update_enquiry_bike_details()
