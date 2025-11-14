window.onload = fetchUserProfile;

function fetchUserProfile() {
    const token = sessionStorage.getItem("token");
    if (!token) {
        window.location.href = "userLogin.html";
        return;
    }

    fetch(`${window.API.BASE_URL}/profile`, {
        headers: { "Authorization": "Bearer " + token }
    })
    .then(res => {
        if (!res.ok) throw new Error("Invalid Token");
        return res.json();
    })
    .then(user => {
        loadUserProfile({
            name: user.firstName + " " + user.lastName,
            email: user.email,
            phone: user.mobileNumber,
            role: "User"
        });
    })
    .catch(() => {
        sessionStorage.removeItem("token");
        window.location.href = "userLogin.html";
    });
}

function loadUserProfile(userProfile) {
    document.getElementById("userProfileName").textContent = userProfile.name;
    document.getElementById("userProfileRole").textContent = userProfile.role;
    document.getElementById("userName").textContent = userProfile.name;
    document.getElementById("userEmail").textContent = userProfile.email;
    document.getElementById("userRole").textContent = userProfile.role;
    document.getElementById("userPhone").textContent = userProfile.phone;
}

function logOutProfile() {
    sessionStorage.removeItem("token");
    Swal.fire({
        icon: "success",
        title: "Logged Out",
        text: "You have been logged out successfully!"
    }).then(() => {
        window.location.href = "index.html";
    });
}

async function MyEnquirys() {
    const token = sessionStorage.getItem("token");

    if (!token) {
        document.getElementById("MyEnquirys").innerHTML =
            `<p class="text-center text-danger">Please log in to view your enquiries.</p>`;
        return;
    }

    let profile = await fetch(`${window.API.BASE_URL}/profile`, {
        headers: { "Authorization": "Bearer " + token }
    }).then(res => res.json());
    fetch(`${window.API.BASE_URL}/enquiries/${profile.mobileNumber}`)
        .then(res => res.json())
        .then(enquiries => {
            fetch(`${window.API.BASE_URL}/bikes`)
                .then(res => res.json())
                .then(bikes => {
                    let html = "";
                    enquiries.forEach(enquiry => {
                        let bike = bikes.find(b => b.id === enquiry.listingId);
                        html += `
                            <div class="col-12 col-md-4 col-lg-3 mb-3">
                                <div class="enquiry-card card shadow-sm">
                                    <div class="card-body">
                                        <h5>${bike ? bike.listingTitle : "Bike Removed"}</h5>
                                        <p><strong>Message:</strong> ${enquiry.message}</p>
                                    </div>
                                </div>
                            </div>`;
                    });

                    document.getElementById("MyEnquirys").innerHTML =
                        enquiries.length
                            ? `<div class="row">${html}</div>`
                            : `<p class="text-center text-muted">No enquiries found.</p>`;
                });
        });
}
