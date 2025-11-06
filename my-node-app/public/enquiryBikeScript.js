function loadServerEnquiries() {
  fetch(`${window.API.BASE_URL}/enquiries`)
    .then(res => res.json())
    .then(data => {
      printEnquiryDetails(data);
    })
    .catch(err => console.error("Error loading enquiries:", err));
}

function printEnquiryDetails(enquiries) {
  let statusValue = document.getElementById("statusFilter").value;
  let output = '';
  enquiries.forEach((enquiry) => {
    if (statusValue === "all" || enquiry.status === statusValue) {
      output += `
        <div class="col-12 col-md-4 col-lg-3 mb-3">
          <div class="enquiry-card card shadow-sm">
            <div class="card-body">
              <h5 class="card-title">Bike Name: ${enquiry.listingTitle}</h5>
              <p><strong>Bike ID:</strong> ${enquiry.listingId}</p>
              <p><strong>Customer Name:</strong> ${enquiry.customerName}</p>
              <p><strong>Mobile:</strong> ${enquiry.mobile}</p>
              <p><strong>Email:</strong> ${enquiry.email}</p>
              <p><strong>Location:</strong> ${enquiry.location}</p>
              <p><strong>Time:</strong> ${enquiry.timestamp}</p>
              <p><strong>Status:</strong> ${enquiry.status || "Not updated"}</p>
              <p><strong>Message:</strong> ${enquiry.message || "Not set"}</p>
              <div id="statusContainer-${enquiry.id}">
                <button class="btn btn-primary" onclick="changeStatus(${enquiry.id})">Edit Status</button>
                <button class="btn btn-primary" onclick="sendMessage(${enquiry.id})">Send Message</button>
              </div>
            </div>
          </div>
        </div>
      `;
    }
  });

  let outputElement = document.getElementById("buyingBikeDetailsAdmin");
  if (outputElement) {
    outputElement.innerHTML = output || "<p>No enquiries found.</p>";
  }
}
document.getElementById("statusFilter").addEventListener("change", () => {
  printEnquiryDetails(enquiries);
});

function changeStatus(key) {
  let container = document.getElementById(`statusContainer-${key}`);

  let options = window.CONFIG.enquiryStatusChangw
    .map(s => `<option value="${s}">${s}</option>`)
    .join("");

  container.innerHTML = `
    <select class="form-select" id="statusSelect-${key}">
      <option value="">Select Status</option>
      ${options}
    </select>
    <button class="btn btn-success mt-2" onclick="saveStatus(${key})">Save</button>
  `;
}

function saveStatus(id) {
  let newStatus = document.getElementById(`statusSelect-${id}`).value;

  fetch(`${window.API.BASE_URL}/enquiries/${id}/status`, {

    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status: newStatus })
  })
    .then(response => response.json())
    .then(data => {
      alert("✅ Status updated successfully!");
      loadServerEnquiries();
    })
    .catch(error => console.error("❌ Error updating status:", error));
}

function sendMessage(key) {
  let container = document.getElementById(`statusContainer-${key}`);
  container.innerHTML = `
    <textarea class="form-control" id="messageInput-${key}" rows="3" placeholder="Type your message here"></textarea>
    <button class="btn btn-success mt-2" onclick="saveMessage(${key})">Send Message</button>
  `;
}

function sendMessage(key) {
  let container = document.getElementById(`statusContainer-${key}`);
  container.innerHTML = `
    <textarea class="form-control" id="messageInput-${key}" rows="3" placeholder="Type your message here"></textarea>
    <button class="btn btn-success mt-2" onclick="saveMessage(${key})">Send Message</button>
  `;
}
function saveMessage(id) {
  let newMessage = document.getElementById(`messageInput-${id}`).value;

  fetch(`${window.API.BASE_URL}/enquiries/${id}/message`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: newMessage })
  })
    .then(response => response.json())
    .then(data => {
      alert("✅ Message updated successfully!");
      loadServerEnquiries();
    })
    .catch(error => {
      console.error("❌ Error updating message:", error);
    });
}

