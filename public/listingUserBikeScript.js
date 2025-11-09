
function loadAllBikeListings() {
  fetch(`${window.API.BASE_URL}/bikes`)
    .then(response => response.json())
    .then(bikeListings => renderAdminBikeListings(bikeListings))
    .catch(err => console.error("Error fetching bikes from server:", err));
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

            ${adminName !== "mani" ? `<p class="price-buying">Buying Price: ${bike.bikePrice}</p>` : ""}

            <p class="price-box">
              Selling Price:
              <span id="sellingPrice-${bike.id}">${bike.sellingPrice || "Not Set"}</span>
            </p>
            <p style="background-color: ${bike.isSoldout ? 'rgba(255,0,0,0.2)' : 'transparent'}; 
                      border-radius: 10px;">
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

            <button type="button" class="button-btn" onclick="soldOut(${bike.id})">Sold Out
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

function acceptBike(id) {
  fetch(`${window.API.BASE_URL}/bikes/${id}/accept`, { method: 'PUT' })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        Swal.fire({
            icon: 'success',
            title: 'Bike Accepted',
            text: 'Bike Accepted successfully.',
            confirmButtonColor: '#28a745',
            confirmButtonText: 'Continue'
        })
        loadAllBikeListings(); 
      }
    })
    .catch(err => console.error("Error accepting bike:", err));
}

function rejectBike(id) {
  fetch(`${window.API.BASE_URL}/bikes/${id}/reject`, { method: 'PUT' })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        Swal.fire({
        icon: 'success',
        title: 'Bike Rejected',
        text: 'Bike Rejected successfully.',
        confirmButtonColor: '#28a745',
        confirmButtonText: 'Continue'
    })
        loadAllBikeListings();
      }
    })
    .catch(err => console.error("Error rejecting bike:", err));
}

function saveNewPrice(bikeId) {
  let newPriceInput = document.getElementById(`newPrice-${bikeId}`);
  let newPrice = parseInt(newPriceInput.value);

  if (isNaN(newPrice) || newPrice <= 0) {
    alert("Please enter a valid price");
    return;
  }

  fetch(`${window.API.BASE_URL}/bikes/${bikeId}/price`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ newPrice })
  })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        document.getElementById(`sellingPrice-${bikeId}`).innerText = newPrice;
        newPriceInput.value = "";
            Swal.fire({
            icon: 'success',
            title: 'Price Saved',
            text: 'New price Saved',
            confirmButtonColor: '#28a745',
            confirmButtonText: 'Continue'
        })
      }
    })
    .catch(err => console.error("Error updating price:", err));
}function soldOut(bikeId) {

  Swal.fire({
    title: "Are you sure?",
    text: "This bike will be moved to Sold Out and removed from active listings.",
    icon: "warning",
    showCancelButton: true,
    confirmButtonColor: "#28a745",
    cancelButtonColor: "#d33",
    confirmButtonText: "Yes, sold out"
  }).then((result) => {

    if (result.isConfirmed) {

      fetch(`${window.API.BASE_URL}/bikes/${bikeId}/soldout`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" }
      })
      .then(res => res.json())
      .then(data => {

        Swal.fire({
          icon: "success",
          title: "Moved to Sold Out",
          text: "This bike is now sold out.",
          confirmButtonColor: "#28a745"
        });
        loadAllBikeListings();

        if (typeof loadSoldOutBikes === "function") {
            loadSoldOutBikes();
        }

      })
      .catch(err => {
        console.error("Error marking bike as sold out:", err);
        Swal.fire("Error", "Failed to update status", "error");
      });
    }
  });

}
