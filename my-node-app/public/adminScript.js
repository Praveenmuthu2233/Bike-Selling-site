document.addEventListener("DOMContentLoaded", () => {
    checkAdminLoginStatus();
    document.getElementById("adminLogin").addEventListener("submit", handleAdminLogin);
});

function handleAdminLogin(event) {
    event.preventDefault();

    let username = document.getElementById("adminName").value.trim();
    let password = document.getElementById("adminPassword").value.trim();

    fetch(`${window.API.BASE_URL}/adminLogin`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
    })
    .then(res => res.json())
    .then(data => {
        if (!data.success) {
            Swal.fire({
                icon: "error",
                title: "Login Failed",
                text: data.message,
                confirmButtonColor: "#d33"
            });
            return;
        }
        saveAdminToken(data.token);
        sessionStorage.setItem("adminName", username);

        Swal.fire({
            icon: "success",
            title: `Welcome ${data.admin.name}!`,
            confirmButtonColor: "#28a745",
            confirmButtonText: "Continue"
        }).then(() => { 
            checkAdminLoginStatus();
        });
    });
}

function checkAdminLoginStatus() {
    let token = sessionStorage.getItem("adminToken");
    let adminLinks = document.getElementById("adminLinks");
    let loginContainer = document.querySelector(".containerAdmin");
    let showName = document.getElementById("adminNameShow");

    if (!token) {
        loginContainer.classList.remove("d-none");
        adminLinks.classList.add("d-none");
        return;
    }
    fetch(`${window.API.BASE_URL}/adminProfile`, {
        headers: { "Authorization": "Bearer " + token }
    })
    .then(res => res.json())
    .then(data => {
        if (!data.success) {
            sessionStorage.removeItem("adminToken");
            return checkAdminLoginStatus();
        }
        console.log(data.admin)
        let admin = data.admin;
        showName.innerHTML = `<h3>Admin ${admin.username}</h3>`;

        loginContainer.classList.add("d-none");
        adminLinks.classList.remove("d-none");
    });
}

document.addEventListener("DOMContentLoaded", () => {
  const logoutBtn = document.getElementById("logoutBtn");
  logoutBtn.addEventListener("click", () => {
    sessionStorage.removeItem("adminToken");
    Swal.fire({
      icon: "success",
      title: "Logged Out",
      confirmButtonColor: "#28a745"
    }).then(() => {
      checkAdminLoginStatus();
      window.location.href = "/my-node-app/public/admin.html";
    });
  });
});

function saveAdminToken(token) {
    sessionStorage.setItem("adminToken", token);
}
