
fetch('galary.json')
  .then(response => response.json())
  .then(data => {
    data.forEach((item, index) => {
      item.id = index + 1;
    });
    saveToIndexedDB(data);
  });

function saveToIndexedDB(dataArray) {
  const request = indexedDB.open("BikesData", 1);

  request.onupgradeneeded = function(event) {
    const db = event.target.result;
    if (!db.objectStoreNames.contains("users")) {
      db.createObjectStore("users", { keyPath: "id" });
    }
  };

  request.onsuccess = function(event) {
    const db = event.target.result;
    const transaction = db.transaction(["users"], "readwrite");
    const store = transaction.objectStore("users");

    dataArray.forEach(item => {
      store.put(item);
    });

    transaction.oncomplete = function () {
      const readTransaction = db.transaction(["users"], "readonly");
      const readStore = readTransaction.objectStore("users");

      const getAllRequest = readStore.getAll();
      getAllRequest.onsuccess = function(event) {
        const categoryImgs = event.target.result;
        catagoryImgsPrint(categoryImgs);
      };
    };
  };
}

function catagoryImgsPrint(catagoryImgs) {
  let catagoryImgsOutPut = "";
  catagoryImgs.forEach(element => {
    catagoryImgsOutPut += `
      <div class="col-12 col-md-6 col-lg-3 category-bike-card text-center">
        <img src="${element.imageUrl}" alt="${element.bikeName}" width="250px">
        <h4>${element.bikeName}</h4>
      </div>`;
  });
  document.getElementById("categoryBikeImg").innerHTML = catagoryImgsOutPut;
}

document.getElementById("applyFilter").addEventListener("click", () => {
    let transaction = db.transaction(["bikesForSale"], "readonly");
    let store = transaction.objectStore("bikesForSale");
    let getAllRequest = store.getAll();

    getAllRequest.onsuccess = function (event) {
        allProducts = event.target.result.filter(b => b.isAccepted);
        applyFilter();
    };
});

function applyFilter() {
    let minPriceFilter = parseInt(document.getElementById("minPrice").value) || 0;
    let maxPriceFilter = parseInt(document.getElementById("maxPrice").value) || Infinity;

    allProducts = allProducts.filter(bike => {
        let bikePrice = parseInt(bike.sellingPrice) || 0;
        return bikePrice >= minPriceFilter && bikePrice <= maxPriceFilter;
    });

    displayProducts(currentPage);
    setupPagination();
}

document.getElementById("bikeForm").addEventListener("submit", function (event) {
  event.preventDefault(); 
  const bikeAddingData = {
    listingTitle: document.getElementById("listingTitle").value,
    vehicleNumber: document.getElementById("vehicleNum").value,
    sellerName: document.getElementById("sellerName").value,
    mobileNum: document.getElementById("mobileNum").value,
    bikeCondition: document.getElementById("Condition").value,
    bikeType: document.getElementById("Type").value,
    makedFrom: document.getElementById("Make").value,
    bikeModel: document.getElementById("bikeModel").value,
    bikeKms: document.getElementById("BikeKMS").value,
    bikePrice: document.getElementById("BikePrice").value,
    sellingPrice: document.getElementById("BikePrice").value,
    bikeOwner: document.getElementById("bikeOwner").value,
    bikeBuyingYear: document.getElementById("bikeYear").value,
    bikeColor: document.getElementById("bikeColor").value,
    bikeEngineCC: document.getElementById("EngineCC").value,
    driveType: document.getElementById("driveType").value,
    insurance: document.getElementById("Insurance").value,
    horsepower: document.getElementById("Horsepower").value,
    bikeLocation: document.getElementById("Location").value,
    description: document.getElementById("description").value,
    isAccepted: false,
    isSoldout: false
  };

  fetch("http://localhost:5000/addBike", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(bikeAddingData)
  })
    .then(response => response.json())
    .then(data => {
      alert(data.message || "Bike added successfully!");
      document.getElementById("bikeForm").reset();
    })
    .catch(err => {
      console.error("Error adding bike:", err);
      alert("Error adding bike. Please try again.");
    });
});

var itemsPerPage
var allProducts = [];
var currentPage

async function loadProducts() {
  currentPage = 1;
  try {
    const response = await fetch("https://bike-selling-site-1.onrender.com/bikes");
    const products = await response.json();
    
    allProducts = products.filter(b => b.isAccepted == 1);

    displayProducts(currentPage);
    setupPagination();
  } catch (err) {
    console.error("Error fetching bikes:", err.message);
  }
}

loadProducts();

function displayProducts(page) {
  itemsPerPage = 8
  let start = (page - 1) * itemsPerPage;
  let end = start + itemsPerPage;
  let paginatedProducts = allProducts.slice(start, end);

  let container = document.getElementById("productList");
  container.innerHTML = "";

  if (paginatedProducts.length === 0) {
    container.innerHTML = `<p class="text-center">No bikes available.</p>`;
    return;
  }

  paginatedProducts.forEach((bike) => {
    let BikePriceShow = bike.sellingPrice || '';
    let card = `
      <div class="col-12 col-md-6 col-lg-3 product-bike-card text-center">
        <img src="${'https://rajaneditz.com/wp-content/uploads/2022/05/Ktm-rcf-2022-png-3.png'}" alt="${bike.makedFrom}" width="230px" height="180px">
        <h5>${bike.listingTitle}</h5>
        <h5>₹ ${BikePriceShow}</h5>
        <div class="m-3">
          <button type="button" class="btn-green" data-bs-toggle="modal" data-bs-target="#viewModal${bike.id}" onclick="populateModal(${bike.id})">View Details</button>
          <button type="button" class="btn-green" data-bs-toggle="modal" data-bs-target="#enquiryModal${bike.id}" onclick="enquiryBike(${bike.id})">Enquiry</button>
        </div>
      </div>
    `;

    let modal = `
      <div class="modal fade" id="viewModal${bike.id}" tabindex="-1" aria-labelledby="viewModalLabel${bike.id}" aria-hidden="true">
        <div class="modal-dialog">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title" id="viewModalLabel${bike.id}">Bike Details</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body" id="viewDetails${bike.id}">
              <h5>Title: ${bike.listingTitle}</h5>
              <p>Vehicle Number: ${bike.vehicleNumber}</p>
              <p>Condition: ${bike.bikeCondition}</p>
              <p>Type: ${bike.bikeType}</p>
              <p>Make: ${bike.makedFrom}</p>
              <p>Model: ${bike.bikeModel}</p>
              <p>Kms: ${bike.bikeKms}</p>
              <p>Price: ${bike.bikePrice}</p>
              <p>Owner: ${bike.bikeOwner}</p>
              <p>Year: ${bike.bikeBuyingYear}</p>
              <p>Color: ${bike.bikeColor}</p>
              <p>Engine CC: ${bike.bikeEngineCC}</p>
              <p>Drive Type: ${bike.driveType}</p>
              <p>Insurance: ${bike.insurance}</p>
              <p>Horsepower: ${bike.horsepower}</p>
              <p>Location: ${bike.bikeLocation}</p>
            </div>
            <div class="modal-footer">
              <button type="button" class="button-btn" data-bs-dismiss="modal">Done</button>
            </div>
          </div>
        </div>
      </div>
    `;

    container.insertAdjacentHTML("beforeend", card + modal);
  });
}

function setupPagination() {
  let totalPages = Math.ceil(allProducts.length / itemsPerPage);
  let paginationContainer = document.getElementById("pagination");
  if (!paginationContainer) return;
  
  paginationContainer.innerHTML = "";
  for (let i = 1; i <= totalPages; i++) {
    let btn = document.createElement("button");
    btn.innerText = i;
    btn.classList.add("page-btn");
    if (i === currentPage) btn.classList.add("active");
    btn.addEventListener("click", () => {
      currentPage = i;
      displayProducts(currentPage);
      setupPagination();
    });
    paginationContainer.appendChild(btn);
  }
}

function setupPagination() {
  let totalPages = Math.ceil(allProducts.length / itemsPerPage);
  let pagination = document.getElementById("pagination");
  pagination.innerHTML = "";

  let prev = document.createElement("li");
  prev.className = "page-item";
  prev.innerHTML = `<a class="page-link" href="#Products">&laquo;</a>`;
  prev.onclick = function () {
    if (currentPage > 1) {
      currentPage--;
      displayProducts(currentPage);
      setupPagination();
    }
  };
  pagination.appendChild(prev);

  for (let i = 1; i <= totalPages; i++) {
    let li = document.createElement("li");
    li.className = "page-item " + (i === currentPage ? "active" : "");
    li.innerHTML = `<a class="page-link" href="#Products">${i}</a>`;
    li.onclick = function () {
      currentPage = i;
      displayProducts(currentPage);
      setupPagination();
    };
    pagination.appendChild(li);
  }

  let next = document.createElement("li");
  next.className = "page-item";
  next.innerHTML = `<a class="page-link" href="#Products">&raquo;</a>`;
  next.onclick = function () {
    if (currentPage < totalPages) {
      currentPage++;
      displayProducts(currentPage);
      setupPagination();
    }
  };
  pagination.appendChild(next);
}


function loadAllBikeListings() {
  fetch("http://localhost:5000/bikes")
    .then(response => response.json())
    .then(bikeListings => renderAdminBikeListings(bikeListings))
    .catch(err => console.error("❌ Error fetching bikes from server:", err));
}

function getCurrentAdmin(callback) {
  let requestDB = indexedDB.open("adminLoginDataBase", 1);

  requestDB.onsuccess = function(event) {
    const dbEnq = event.target.result;
    let transaction = dbEnq.transaction(["admins"], "readonly");
    let objectStore = transaction.objectStore("admins");
    let getAll = objectStore.getAll();

    getAll.onsuccess = function () {
      let admins = getAll.result || [];
      let loggedInAdmin = admins.find(admin => admin.isAdminLogin === true);
      if (callback) callback(loggedInAdmin ? loggedInAdmin.name : null);
    };
  };
}

function renderAdminBikeListings(bikeListings) {
  getCurrentAdmin(function(adminName) {
    let output = "";

    bikeListings.forEach(bike => {
      output += `
        <div class="col-12 col-md-6 col-lg-3">
          <img src="${bike.image}" alt="${bike.makedFrom}" width="230px" height="180px">
          <div class="m-3">
            <h5>Title: ${bike.listingTitle}</h5>
            <p>Vehicle Number: ${bike.vehicleNumber}</p>
            <p>Seller Name: ${bike.sellerName}</p>
            <p>Mobile Number: ${bike.mobileNum}</p>
            <p>Make: ${bike.makedFrom}</p>
            <p>Model: ${bike.bikeModel}</p>
            <p>Kms: ${bike.bikeKms}</p>

            ${adminName !== "mani" ? `<p>Buying Price: ${bike.bikePrice}</p>` : ""}

            <p>
              Selling Price: 
              <span id="sellingPrice-${bike.id}">${bike.sellingPrice || "Not Set"}</span>
            </p>

            <p style="background-color: ${bike.isSoldout ? 'rgba(255,0,0,0.2)' : 'transparent'}; 
                      border-radius: 10px; padding: 10px 3px; margin-bottom: 15px;">
              Is sold out: ${bike.isSoldout ? "Yes" : "No"}
            </p>

            <p>Owner: ${bike.bikeOwner}</p>
            <p>Year: ${bike.bikeBuyingYear}</p>
          </div>

          <div>
            ${adminName !== "mani" ? `
              <input type="number" id="newPrice-${bike.id}" placeholder="Enter new price" class="form-control mb-2">
              <button class="button-btn" onclick="saveNewPrice(${bike.id})">Save Price</button>
            ` : ""}

            <button type="button" class="button-btn" onclick="soldOut(${bike.id})" 
              ${bike.isSoldout ? "disabled" : ""}>
              Sold Out
            </button>
          </div>

          <button class="button-btn" onclick="rejectBike(${bike.id})">Reject</button>
          <button class="button-btn" onclick="acceptBike(${bike.id})">Accept</button>
        </div>
      `;
    });

    const bikeDetailsContainer = document.getElementById("sellingBikeDetailsAdmin");
    if (bikeDetailsContainer) bikeDetailsContainer.innerHTML = output;
  });
}

loadAllBikeListings();


function soldOut(bikeId) {

  fetch(`http://localhost:5000/bikes/${bikeId}/soldout`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" }
  })
  .then(res => res.json())
  .then(data => {
    alert(data.message);
    loadAllBikeListings();
  })
  .catch(err => console.error("Error:", err));
}

function soldOutPrint() {
  
  fetch('https://bike-selling-site-1.onrender.com/soldout')
    .then(res => res.json())
    .then(bikeListings => {
      const bikeDetailsContainer = document.getElementById("SoldOut");

      if (bikeListings.length === 0) {
        bikeDetailsContainer.innerHTML = "<p class='text-center text-muted'>No bikes sold out yet.</p>";
        return;
      }

      let output = "";
      bikeListings.forEach(bike => {
        
        output += `
          <div class="col-12 col-md-6 col-lg-3">
            <div class="sold-out-card">
              <div class="sold-out-badge">SOLD OUT <span class="red"> BIKE ID ${bike.originalBikeId}</span></div>
              <img src="${bike.image}" alt="${bike.makedFrom}" class="img-fluid rounded" style="max-height:180px; object-fit:cover;"></img>
              <div class="m-3">
                <h5>Title: ${bike.listingTitle}</h5>
                <p>Vehicle Number: ${bike.vehicleNumber}</p>
                <p>Seller Name: ${bike.sellerName}</p>
                <p>Mobile Number: ${bike.mobileNum}</p>
                <p>Make: ${bike.makedFrom}</p>
                <p>Model: ${bike.bikeModel}</p>
                <p>Kms: ${bike.bikeKms}</p>
                <p>Selling Price: ${bike.sellingPrice}</p>
                <p>Buying Price: ${bike.bikePrice}</p>
                <p>Owner: ${bike.bikeOwner}</p>
                <p>Year: ${bike.bikeBuyingYear}</p>
              </div>
              <h3>Profit : ${bike.sellingPrice - bike.bikePrice}</h3>
            </div>
          </div>
        `;
      });

      bikeDetailsContainer.innerHTML = output;
    })
    .catch(err => console.error("Error fetching sold-out bikes:", err));
}

function saveNewPrice(bikeId) {
  let newPriceInput = document.getElementById(`newPrice-${bikeId}`);
  let newPrice = parseInt(newPriceInput.value);

  if (isNaN(newPrice) || newPrice <= 0) {
    alert("Please enter a valid price");
    return;
  }

  fetch(`http://localhost:5000/bikes/${bikeId}/price`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ newPrice })
  })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        document.getElementById(`sellingPrice-${bikeId}`).innerText = newPrice;
        newPriceInput.value = "";
        alert("Selling price updated successfully!");
      }
    })
    .catch(err => console.error("Error updating price:", err));
}

function acceptBike(id) {
  fetch(`http://localhost:5000/bikes/${id}/accept`, { method: 'PUT' })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        alert("Bike Accepted");
        loadAllBikeListings(); 
      }
    })
    .catch(err => console.error("Error accepting bike:", err));
}

function rejectBike(id) {
  fetch(`http://localhost:5000/bikes/${id}/reject`, { method: 'PUT' })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        alert("Bike Rejected");
        loadAllBikeListings();
      }
    })
    .catch(err => console.error("Error rejecting bike:", err));
}



function populateModal(bikeId) {
  let transaction = db.transaction(["bikesForSale"], "readonly");
  let store = transaction.objectStore("bikesForSale");
  let getRequest = store.get(bikeId);

  getRequest.onsuccess = function (event) {
    const bike = event.target.result;
    const modalContent = `
      <h5>Title: ${bike.listingTitle}</h5>
      <p>Vehicle Number: ${bike.vehicleNumber}</p>
      <p>Condition: ${bike.bikeCondition}</p>
      <p>Type: ${bike.bikeType}</p>
      <p>Make: ${bike.makedFrom}</p>
      <p>Model: ${bike.bikeModel}</p>
      <p>Kms: ${bike.bikeKms}</p>
      <p>Price: ${bike.bikePrice}</p>
      <p>Owner: ${bike.bikeOwner}</p>
      <p>Year: ${bike.bikeBuyingYear}</p>
      <p>Color: ${bike.bikeColor}</p>
      <p>Engine CC: ${bike.bikeEngineCC}</p>
      <p>Drive Type: ${bike.driveType}</p>
      <p>Insurance: ${bike.insurance}</p>
      <p>Horsepower: ${bike.horsepower}</p>
      <p>Location: ${bike.bikeLocation}</p>
    `;
    document.getElementById(`viewDetails${bike.id}`).innerHTML = modalContent;
  };
}

function enquiryBike(bikeId) {
  //fetch(`https://bike-selling-site-1.onrender.com/soldout${bikeId}`)
  fetch(`https://bike-selling-site-1.onrender.com/bikes/${bikeId}`)
    .then(response => response.json())
    .then(bike => {
      if (!bike) {
        alert("Bike not found!");
        return;
      }

      let enquiryModal = `
        <div class="modal fade" id="enquiryModal${bike.id}" tabindex="-1" role="dialog" aria-labelledby="enquiryModalLabel${bike.id}" aria-hidden="true">
          <div class="modal-dialog" role="document">
            <div class="modal-content">
              <div class="modal-header">
                <h5 class="modal-title" id="enquiryModalLabel${bike.id}">Enquiry for ${bike.listingTitle} ${bike.bikeBuyingYear}</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
              </div>
              <div class="modal-body">
                <form id="enquiryForm${bike.id}">
                  <div class="mb-3">
                    <label for="userName${bike.id}" class="form-label">Your Name<span class="text-danger">*</span></label>
                    <input type="text" class="form-control" id="userName${bike.id}" required>
                  </div>
                  <div class="mb-3">
                    <label for="mobileNumber${bike.id}" class="form-label">Mobile Number<span class="text-danger">*</span></label>
                    <input type="text" class="form-control" id="mobileNumber${bike.id}" required>
                  </div>
                  <div class="mb-3">
                    <label for="emailContact${bike.id}" class="form-label">Email<span class="text-danger">*</span></label>
                    <input type="email" class="form-control" id="emailContact${bike.id}">
                  </div>
                  <div class="mb-3">
                    <label for="Location${bike.id}" class="form-label">Location</label>
                    <input type="text" class="form-control" id="Location${bike.id}" required>
                  </div>
                  <div class="d-flex flex-row justify-content-end">
                    <button type="submit" class="btn btn-primary">Submit Enquiry</button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        </div>
      `;

      document.body.insertAdjacentHTML('beforeend', enquiryModal);

      document.getElementById(`enquiryForm${bike.id}`).addEventListener('submit', function (event) {
        event.preventDefault();
        submitEnquiry(bike.id);

        const modal = bootstrap.Modal.getInstance(document.getElementById(`enquiryModal${bike.id}`));
        modal.hide();
      });

      const modal = new bootstrap.Modal(document.getElementById(`enquiryModal${bike.id}`));
      modal.show();
    })
    .catch(err => console.error("Error fetching bike details:", err));
}

function submitEnquiry(id) {
  let userName = document.getElementById(`userName${id}`).value.trim();
  let mobileNumber = document.getElementById(`mobileNumber${id}`).value.trim();
  let emailContact = document.getElementById(`emailContact${id}`).value.trim();
  let location = document.getElementById(`Location${id}`).value.trim();

  if (!userName || !/^[0-9]{10}$/.test(mobileNumber) || !/^\S+@\S+\.\S+$/.test(emailContact) || !location) {
      alert("Please fill all fields correctly.");
      return;
  }

  //fetch(`http://localhost:5000/bikes/${id}`)
  fetch(`https://bike-selling-site-1.onrender.com/bikes/${id}`)
    .then(res => res.json())
    .then(bike => {
      let now = new Date();
      const formatted = `${now.getDate().toString().padStart(2,'0')}/${(now.getMonth()+1).toString().padStart(2,'0')}/${now.getFullYear()} ${now.getHours().toString().padStart(2,'0')}:${now.getMinutes().toString().padStart(2,'0')}`;

      const enquiryData = {
          listingId: bike.id,
          listingTitle: bike.listingTitle,
          customerName: userName,
          mobile: mobileNumber,
          email: emailContact,
          location: location,
          timestamp: formatted
      };

      fetch("https://bike-selling-site-1.onrender.com/bikes/submitEnquiry", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(enquiryData)
      })
      .then(res => res.json())
      .then(data => {
          alert("✅ Enquiry submitted successfully!");
          console.log(data);
      })
      .catch(err => console.error(err));
    })
    .catch(err => console.error(err));
}


function loadServerEnquiries() {
  fetch("https://bike-selling-site-1.onrender.com/enquiries")
    .then(res => res.json())
    .then(data => {
      console.log("Hi")
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
  container.innerHTML = `
    <select class="form-select" id="statusSelect-${key}">
      <option value="">Select Status</option>
      <option value="Cold">Cold</option>
      <option value="Warm">Warm</option>
      <option value="Hot">Hot</option>
    </select>
    <button class="btn btn-success mt-2" onclick="saveStatus(${key})">Save</button>
  `;
}
function saveStatus(id) {
  let newStatus = document.getElementById(`statusSelect-${id}`).value;

  fetch(`http://localhost:5000/enquiries/${id}/status`, {
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

  fetch(`http://localhost:5000/enquiries/${id}/message`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: newMessage })
  })
    .then(response => response.json())
    .then(data => {
      alert("✅ Message updated successfully!");
      loadServerEnquiries();
    })
    .catch(error => console.error("❌ Error updating message:", error));
}

