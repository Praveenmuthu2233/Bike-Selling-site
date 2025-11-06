let loggedInUser = null
let loginDB

let request = indexedDB.open("signUpDetailsDB", 1)

request.onsuccess = function(event) {
    loginDB = event.target.result
    const transaction = loginDB.transaction(["signUpList"], "readonly")
    const objectStore = transaction.objectStore("signUpList")
    const getAllRequest = objectStore.getAll()

    getAllRequest.onsuccess = function(event) {
        const users = event.target.result
        if (users.length > 0) {
            for (let i = 0; i < users.length; i++) {
                if (users[i].isLogin === true) {
                    loggedInUser = users[i]
                    break
                }
            }
            if (loggedInUser) {
                const userProfile = {
                    name: loggedInUser.firstName + " " + loggedInUser.lastName,
                    email: loggedInUser.email,
                    role: "User",
                    phone: loggedInUser.mobileNumber
                }
                loadUserProfile(userProfile)
            }
        }
    }
}

function loadUserProfile(userProfile) {
    document.getElementById("userProfileName").textContent = userProfile.name
    document.getElementById("userProfileRole").textContent = userProfile.role
    document.getElementById("userName").textContent = userProfile.name
    document.getElementById("userEmail").textContent = userProfile.email
    document.getElementById("userRole").textContent = userProfile.role
    document.getElementById("userPhone").textContent = userProfile.phone
}

function logOutProfile() {
  const tx = loginDB.transaction(['signUpList'], 'readwrite');
  const store = tx.objectStore('signUpList');
  const req = store.openCursor();

  let loggedOut = false;

  req.onsuccess = function (event) {
    const cursor = event.target.result;
    if (!cursor) {
      if (!loggedOut) {
        Swal.fire({
          icon: 'info',
          title: 'Already Logged Out',
          text: 'No active user session found.',
          confirmButtonColor: '#0d6efd',
          confirmButtonText: 'OK'
        });
      }
      return;
    }

    const user = cursor.value;
    if (user.isLogin) {
      user.isLogin = false;
      cursor.update(user).onsuccess = function () {
        loggedOut = true;
        Swal.fire({
          icon: 'success',
          title: 'Logged Out',
          text: 'You have been logged out successfully.',
          confirmButtonColor: '#28a745',
          confirmButtonText: 'Continue'
        }).then(() => {
          window.location.href = 'index.html';
        });
      };
      return;
    }

    cursor.continue();
  };
}

async function  MyEnquirys() {
    let loginDBReq = indexedDB.open("signUpDetailsDB", 1);
    loginDBReq.onsuccess = function (event) {
        let loginDB = event.target.result;
        let tx = loginDB.transaction(["signUpList"], "readonly");
        let store = tx.objectStore("signUpList");
        let getAllReq = store.getAll();

        getAllReq.onsuccess = function () {
            let allUsers = getAllReq.result;
            let loggedInUser = allUsers.find(u => u.isLogin === true);

            if (!loggedInUser) {
                document.getElementById("MyEnquirys").innerHTML = `
                    <p class="text-center text-danger">Please log in to view your enquiries.</p>`;
                return;
            }

            let userMobile = loggedInUser.mobileNumber;

            fetch("https://bike-selling-site-1.onrender.com/enquiries")
                .then(res => res.json())
                .then(allEnquiries => {
                    console.log("All Enquiries:", allEnquiries);

                    let userEnquiries = allEnquiries.filter(
                        enquiry => enquiry.mobile === userMobile
                    );
                    fetch("https://bike-selling-site-1.onrender.com/bikes")
                        .then(res => res.json())
                        .then(allBikes => {
                            console.log("All Bikes:", allBikes);

                            let output = "";
                            userEnquiries.forEach((enquiry) => {
                                let bike = allBikes.find(b => b.id === enquiry.listingId);

                                if (!bike) {
                                    output += `
                                        <div class="col-12 col-md-4 col-lg-3 mb-3">
                                            <div class="enquiry-card card shadow-sm">
                                                <div class="card-body">
                                                    <h5 class="card-title">Bike ID: ${enquiry.listingId}</h5>
                                                    <p><em>This bike no longer exists in the system.</em></p>
                                                </div>
                                            </div>
                                        </div>
                                    `;
                                } else {
                                    output += `
                                        <div class="col-12 col-md-4 col-lg-3 mb-3">
                                            <div class="enquiry-card card shadow-sm">
                                                <div class="card-body">
                                                    <h5 class="card-title">Listing Title: ${bike.listingTitle}</h5>
                                                    <p><strong>Bike ID:</strong> ${bike.id}</p>
                                                    <p><strong>Vehicle Number:</strong> ${bike.vehicleNumber}</p>
                                                    <p><strong>Price:</strong> ₹${bike.bikePrice}</p>
                                                    <p><strong>Buying Year:</strong> ${bike.bikeBuyingYear}</p>
                                                    <p><strong>Message:</strong> ${enquiry.message}</p>
                                                </div>
                                            </div>
                                        </div>
                                    `;
                                }
                            });

                            let outputElement = document.getElementById("MyEnquirys");
                            if (outputElement) {
                                if (userEnquiries.length === 0) {
                                    outputElement.innerHTML = `
                                        <p class="text-center text-muted">No enquiries found.</p>`;
                                } else {
                                    outputElement.innerHTML = `<div class="row">${output}</div>`;
                                }
                            }
                        })
                        .catch(err => {
                            console.error("Error loading bikes:", err);
                        });
                })
                .catch(err => {
                    console.error("Error loading enquiries:", err);
                });
        };
    };

    loginDBReq.onerror = function () {
        console.error("Failed to open IndexedDB.");
    };
}
