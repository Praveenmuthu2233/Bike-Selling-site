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

document.getElementById("applyFilter").addEventListener("click", async () => {
    try {
        //const response = await fetch("https://bike-selling-site-1.onrender.com/bikes");
        const response = await fetch(`${window.API.BASE_URL}/bikes`);
        const products = await response.json();

        allProducts = products.filter(bike => bike.isAccepted == 1);
       
        applyFilter();
    } 
    catch (err) {
        console.error("Error loading bikes for filter:", err);
    }
});

function applyFilter() {
    let minPriceFilter = parseInt(document.getElementById("minPrice").value) || 0;
    let maxPriceFilter = parseInt(document.getElementById("maxPrice").value) || Infinity;

    let filteredProducts = allProducts.filter(bike => {
        let bikePrice = parseInt(bike.sellingPrice) || 0;
        return bikePrice >= minPriceFilter && bikePrice <= maxPriceFilter;
    });

    allProducts = filteredProducts;
    currentPage = 1;
    displayProducts(currentPage);
    setupPagination();
}


// document.getElementById("bikeForm").addEventListener("submit", function (event) {
//   event.preventDefault(); 
//   const bikeAddingData = {
//     //image : document.getElementById("imageUpload").value,
//     listingTitle: document.getElementById("listingTitle").value,
//     vehicleNumber: document.getElementById("vehicleNum").value,
//     sellerName: document.getElementById("sellerName").value,
//     mobileNum: document.getElementById("mobileNum").value,
//     bikeCondition: document.getElementById("Condition").value,
//     bikeType: document.getElementById("Type").value,
//     makedFrom: document.getElementById("Make").value,
//     bikeModel: document.getElementById("bikeModel").value,
//     bikeKms: document.getElementById("BikeKMS").value,
//     bikePrice: document.getElementById("BikePrice").value,
//     sellingPrice: document.getElementById("BikePrice").value,
//     bikeOwner: document.getElementById("bikeOwner").value,
//     bikeBuyingYear: document.getElementById("bikeYear").value,
//     bikeColor: document.getElementById("bikeColor").value,
//     bikeEngineCC: document.getElementById("EngineCC").value,
//     driveType: document.getElementById("driveType").value,
//     insurance: document.getElementById("Insurance").value,
//     horsepower: document.getElementById("Horsepower").value,
//     bikeLocation: document.getElementById("Location").value,
//     description: document.getElementById("description").value,
//     isAccepted: false,
//     isSoldout: false
//   };
//   fetch(window.API.userAddBike, {
//   method: "POST",
//   headers: {
//     "Content-Type": "application/json"
//   },
//   body: JSON.stringify(bikeAddingData)
// })
//   .then(response => response.json())
//   .then(data => {
//     alert(data.message || "Bike added successfully!");
//     document.getElementById("bikeForm").reset();
//   })
//   .catch(err => {
//     console.error("Error adding bike:", err);
//     alert("Error adding bike. Please try again.");
//   });
// });

var itemsPerPage
var allProducts = [];
var currentPage

async function loadProducts() {
  currentPage = 1;
  try {
    const response = await fetch(`${window.API.BASE_URL}/bikes`)
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
  itemsPerPage = window.CONFIG.paginationItemPerPage
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
  let totalPages = Math.ceil(allProducts.length / window.CONFIG.paginationItemPerPage);
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

document.addEventListener("DOMContentLoaded", function () {
  loadGallery();
});

function loadGallery() {
  const galleryContainer = document.getElementById("galleryImages");
  if (!galleryContainer) {
    console.error("galleryImages element not found");
    return;
  }

  if (!Array.isArray(window.gallery_image)) {
    console.error("gallery_image config missing");
    return;
  }

  let html = "";

  window.gallery_image.forEach((img, index) => {
    html += `
      <div class="carousel-item ${index === 0 ? "active" : ""}">
        <img src="${img.url}" class="d-block w-100" alt="${img.alt}">
      </div>
    `;
  });

  galleryContainer.innerHTML = html;
}

function populateModal(bikeId) {
  fetch(`${window.API.BASE_URL}/bikes/${bikeId}`)
    .then(res => res.json())
    .then(bike => {
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

      document.getElementById(`viewDetails${bikeId}`).innerHTML = modalContent;
    })
    .catch(err => {
      console.error("Error fetching bike details:", err);
      document.getElementById(`viewDetails${bikeId}`).innerHTML = 
        "<p class='text-danger'>Failed to load details.</p>";
    });
}


function enquiryBike(bikeId) {
  //fetch(`https://bike-selling-site-1.onrender.com/soldout${bikeId}`)
  fetch(`${window.API.BASE_URL}/bikes/${bikeId}`)
    .then(response => response.json())
    .then(bike => {

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

  if (userName.length < window.VALIDATION.firstNameMin) {
      Swal.fire({
          icon: 'error',
          title: 'Invalid Name',
          text: window.VALIDATION.MESSAGES.firstName,
      });
      return;
  }

  if (!window.VALIDATION.mobileRegex.test(mobileNumber)) {
      Swal.fire({
          icon: 'error',
          title: 'Invalid Mobile Number',
          text: window.VALIDATION.MESSAGES.mobile,
      });
      return;
  }

  if (emailContact && !window.VALIDATION.emailRegex.test(emailContact)) {
      Swal.fire({
          icon: 'error',
          title: 'Invalid Email',
          text: window.VALIDATION.MESSAGES.email,
      });
      return;
  }

  fetch(`${window.API.BASE_URL}/bikes/${id}`)
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

      fetch(`${window.API.BASE_URL}/enquiries`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(enquiryData)
      })
      .then(res => res.json())
      .then(data => {
          Swal.fire({
            icon: 'success',
            title: 'Enquiry Sent!',
            text: 'We will contact you soon.',
            confirmButtonColor: '#28a745',
            confirmButtonText: 'OK'
          });

          console.log(data);
      })
      .catch(err => console.error(err));
    })
    .catch(err => console.error(err));
}

