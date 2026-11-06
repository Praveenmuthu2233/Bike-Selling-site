import sys

marketplace_file = 'my-node-app/static/marketplace.js'
with open(marketplace_file, 'r', encoding='utf-8') as f:
    text = f.read()

start_marker = "function openEnquiryModal(bikeId) {"
idx_start = text.find(start_marker)
assert idx_start != -1

end_marker = "closeModal('enquiry-modal');\n    form.reset();\n  } catch (err) {\n    showToast(err.message || 'Failed to submit enquiry', 'error');\n  } finally {\n    submitBtn.disabled = false;\n    submitBtn.innerHTML = originalHtml;\n  }\n}"
idx_end = text.find(end_marker)
assert idx_end != -1
idx_end += len(end_marker)

new_enquiry_logic = """const pendingEnquiriesInFlight = {};

async function openEnquiryModal(bikeId, triggerBtn = null) {
  const bike = allBikes.find(b => b.id === bikeId);
  if (!bike) return;
  currentBikeForEnquiry = bike;

  const user = AuthService.getUser();
  const token = localStorage.getItem('token') || sessionStorage.getItem('token');

  // Scenario A: User is already logged in -> Submit automatically without showing form
  if (user && token) {
    if (pendingEnquiriesInFlight[bikeId]) {
      showToast('Enquiry already submitted. SMR Motors team is reviewing it.', 'info');
      return;
    }
    pendingEnquiriesInFlight[bikeId] = true;
    if (triggerBtn) {
      triggerBtn.disabled = true;
      triggerBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Submitting...';
    }

    try {
      const payload = {
        bike_id: bike.id,
        user_id: user.id,
        name: user.name || 'Valued Customer',
        email: user.email || '',
        phone: user.phone || '',
        bike_title: `${bike.year || ''} ${bike.title}`,
        message: `Direct booking enquiry for ${bike.brand} ${bike.model} (${bike.year || ''}) from authenticated rider ${user.name}.`
      };

      const res = await apiRequest('/api/enquiries', {
        method: 'POST',
        body: payload
      });

      showToast(res.message || 'Enquiry submitted successfully! SMR Motors team will contact you shortly.', 'success');
      if (triggerBtn) {
        triggerBtn.innerHTML = '<i class="fas fa-check"></i> Enquiry Sent';
      }
    } catch (err) {
      showToast(err.message || 'Failed to submit enquiry', 'error');
      if (triggerBtn) {
        triggerBtn.disabled = false;
        triggerBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Book Test Ride';
      }
    } finally {
      setTimeout(() => {
        delete pendingEnquiriesInFlight[bikeId];
      }, 5000);
    }
    return;
  }

  // Scenario B: User is not logged in -> Display guest enquiry form
  const modalTitle = document.getElementById('enquiry-modal-bike-title');
  if (modalTitle) modalTitle.innerText = `${bike.year || ''} ${bike.title} (₹${Number(bike.price).toLocaleString('en-IN')})`;

  const nameInput = document.getElementById('enquiry-name');
  const emailInput = document.getElementById('enquiry-email');
  const phoneInput = document.getElementById('enquiry-phone');
  if (nameInput) nameInput.value = '';
  if (emailInput) emailInput.value = '';
  if (phoneInput) phoneInput.value = '';

  openModal('enquiry-modal');
}

async function submitEnquiry(event) {
  event.preventDefault();
  if (!currentBikeForEnquiry) return;

  const form = event.target;
  const submitBtn = form.querySelector('button[type="submit"]');
  const originalHtml = submitBtn.innerHTML;
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Submitting...';

  const formData = new FormData(form);
  const name = formData.get('name')?.trim();
  const email = formData.get('email')?.trim();
  const phone = formData.get('phone')?.trim();

  if (!name || !email || !phone) {
    showToast('Please enter your name, email, and mobile number', 'warning');
    submitBtn.disabled = false;
    submitBtn.innerHTML = originalHtml;
    return;
  }

  const payload = {
    bike_id: currentBikeForEnquiry.id,
    bike_title: `${currentBikeForEnquiry.year || ''} ${currentBikeForEnquiry.title}`,
    name: name,
    email: email,
    phone: phone,
    message: formData.get('message') || 'Guest inquiry from website'
  };

  try {
    const res = await apiRequest('/api/enquiries', {
      method: 'POST',
      body: payload
    });
    showToast(res.message || 'Enquiry submitted successfully! SMR Motors team will contact you shortly.', 'success');
    closeModal('enquiry-modal');
    form.reset();
  } catch (err) {
    showToast(err.message || 'Failed to submit enquiry', 'error');
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = originalHtml;
  }
}"""

text = text[:idx_start] + new_enquiry_logic + text[idx_end:]
with open(marketplace_file, 'w', encoding='utf-8') as f:
    f.write(text)

print("Updated marketplace.js with Smart Enquiry Form logic!")
