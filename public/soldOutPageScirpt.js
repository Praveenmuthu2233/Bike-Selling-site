
function soldOutPrint() {
  getCurrentAdmin(adminName => {

    fetch(`${window.API.BASE_URL}/soldout`)
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
                <div class="sold-out-badge">SOLD OUT <span class="green"> BIKE ID ${bike.originalBikeId}</span></div>

                <img src="${bike.image}" alt="${bike.makedFrom}" class="img-fluid rounded"
                     style="max-height:180px; object-fit:cover;">

                <div class="m-3">
                  <h5>Title: ${bike.listingTitle}</h5>
                  <p>Vehicle Number: ${bike.vehicleNumber}</p>
                  <p>Seller Name: ${bike.sellerName}</p>
                  <p>Mobile Number: ${bike.mobileNum}</p>
                  <p>Make: ${bike.makedFrom}</p>
                  <p>Model: ${bike.bikeModel}</p>
                  <p>Kms: ${bike.bikeKms}</p>

                  ${
                    adminName !== "mani"
                      ? `<p>Selling Price: ${bike.sellingPrice}</p>`
                      : ""
                  }

                  ${
                    adminName !== "mani"
                      ? `<p>Buying Price: ${bike.bikePrice}</p>`
                      : ""
                  }

                  <p>Owner: ${bike.bikeOwner}</p>
                  <p>Year: ${bike.bikeBuyingYear}</p>
                </div>

                ${
                  adminName !== "mani"
                    ? `<h3>Profit : ${bike.sellingPrice - bike.bikePrice}</h3>`
                    : ""
                }
              </div>
            </div>
          `;
        });

        bikeDetailsContainer.innerHTML = output;
      })
      .catch(err => console.error("Error fetching sold-out bikes:", err));
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

