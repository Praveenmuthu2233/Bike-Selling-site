let currentPage = 1;
let allEnquiries = [];

function loadServerEnquiries() {
  fetch(`${window.API.BASE_URL}/enquiries`)
    .then(res => res.json())
    .then(data => {
      data.reverse();
      allEnquiries = data;
      currentPage = 1;
      printEnquiryDetails();
    })
    .catch(err => console.error("Error loading enquiries:", err));
}

function loadStatusFilterOptions() {
  let filter = document.getElementById("statusFilter");
  filter.innerHTML = `<option value="all">All Status</option>`;
  window.CONFIG.enquiryStatusList.forEach(status => {
    filter.innerHTML += `<option value="${status}">${status}</option>`;
  });
  filter.innerHTML += `<option value="Not updated">Not updated</option>`;
}
document.addEventListener("DOMContentLoaded", loadStatusFilterOptions);

function printEnquiryDetails() {
  let statusValue = document.getElementById("statusFilter").value;

  let filtered = allEnquiries.filter(e => {
    let status = e.status && e.status.trim() !== "" ? e.status : "Not updated";
    return statusValue === "all" || status === statusValue;
  });

  let perPage = window.CONFIG.enquiriesPerPage;
  let start = (currentPage - 1) * perPage;
  let end = start + perPage;

  let pageData = filtered.slice(start, end);

  let output = "";

  pageData.forEach((enquiry) => {
    let enquiryStatus = enquiry.status && enquiry.status.trim() !== "" ? enquiry.status : "Not updated";

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
            <p><strong>Bike Details:</strong> 
              <a href="${window.API.BASE_URL}/bikes/${enquiry.listingId}" target="_blank">
                Bike Link
              </a>
            </p>
            <p><strong>Status:</strong> 
              <span class="status-text ${enquiryStatus.toLowerCase()}">${enquiryStatus}</span>
            </p>
            <div id="statusContainer-${enquiry.id}">
            <button class="btn btn-primary" onclick="changeStatus(${enquiry.id})">Edit Status</button>
            <button class="btn btn-primary" onclick="sendMessage(${enquiry.id})">Send Message</button>
            <button class="btn btn-danger" onclick="deleteEnquiry(${enquiry.id})">Delete</button>
            </div>
          </div>
        </div>
      </div>
    `;
  });

  document.getElementById("buyingBikeDetailsAdmin").innerHTML = output || "<p>No enquiries found.</p>";
  renderPagination(filtered.length, perPage);
}

document.getElementById("statusFilter").addEventListener("change", () => {
  currentPage = 1;
  printEnquiryDetails();
});

function renderPagination(totalItems, perPage) {
  let totalPages = Math.ceil(totalItems / perPage);
  let paginationDiv = document.getElementById("pagination");

  let maxVisible = 3;
  let start = Math.max(1, currentPage - 1);
  let end = Math.min(totalPages, start + maxVisible - 1);

  if (end - start < maxVisible - 1) {
    start = Math.max(1, end - maxVisible + 1);
  }

  let buttons = `
    <button class="btn btn-sm btn-light me-2" onclick="goToPrevPage()">
      <i class="bi bi-chevron-double-left"></i>
    </button>
  `;
  for (let i = start; i <= end; i++) {
    buttons += `
      <button 
        class="btn btn-sm ${i === currentPage ? 'btn-dark' : 'btn-light'} me-1"
        onclick="goToPage(${i})">
        ${i}
      </button>
    `;
  }
  buttons += `
    <button class="btn btn-sm btn-light ms-2" onclick="goToNextPage(${totalPages})">
      <i class="bi bi-chevron-double-right"></i>
    </button>
  `;
  paginationDiv.innerHTML = buttons;
}

function goToPrevPage() {
  if (currentPage > 1) {
    currentPage--;
    printEnquiryDetails();
  }
}

function goToNextPage(totalPages) {
  if (currentPage < totalPages) {
    currentPage++;
    printEnquiryDetails();
  }
}


function goToPage(page) {
  currentPage = page;
  printEnquiryDetails();
}

async function deleteEnquiry(id) {
  Swal.fire({
    title: "Are you sure?",
    text: "This enquiry will be permanently deleted!",
    icon: "warning",
    showCancelButton: true,
    confirmButtonColor: "#d33",
    cancelButtonColor: "#3085d6",
    confirmButtonText: "Yes, delete it!"
  }).then(async (result) => {
    if (result.isConfirmed) {
      try {
        const res = await fetch(`${window.API.BASE_URL}/deleteEnquiry/${id}`, {
          method: "DELETE"
        });
        await res.json();
        Swal.fire({
          title: "Deleted!",
          text: "Enquiry permanently deleted!",
          icon: "success"
        });
        loadServerEnquiries();
      } catch (err) {
        Swal.fire("Error", "Unable to delete enquiry.", "error");
      }
    }
  });
}

function changeStatus(id) {
  let container = document.getElementById(`statusContainer-${id}`);
  let options = window.CONFIG.enquiryStatusList.map(s => `<option value="${s}">${s}</option>`).join("");
  container.innerHTML = `
    <select class="form-select" id="statusSelect-${id}">
      <option value="">Select Status</option>
      ${options}
    </select>
    <button class="btn btn-success mt-2" onclick="saveStatus(${id})">Save</button>
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
    .then(() => {
      Swal.fire({
        icon: 'success',
        title: 'Status Updated!',
        text: 'Status updated successfully.',
        confirmButtonColor: '#28a745',
        confirmButtonText: 'Continue'
      });
      loadServerEnquiries();
    });
}

function sendMessage(id) {
  let container = document.getElementById(`statusContainer-${id}`);
  container.innerHTML = `
    <textarea class="form-control" id="messageInput-${id}" rows="3" placeholder="Type your message here"></textarea>
    <button class="btn btn-success mt-2" onclick="saveMessage(${id})">Send Message</button>
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
    .then(() => {
      Swal.fire({
        icon: 'success',
        title: 'Message Updated!',
        text: 'Message updated successfully.',
        confirmButtonColor: '#28a745',
        confirmButtonText: 'Continue'
      });
      loadServerEnquiries();
    });
}