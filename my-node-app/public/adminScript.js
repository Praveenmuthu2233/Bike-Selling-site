// let dbEnq;
// let requestDB = indexedDB.open("adminLoginDataBase", 1);

// requestDB.onupgradeneeded = function (event) {
//     dbEnq = event.target.result;
//     if (!dbEnq.objectStoreNames.contains("admins")) {
//         let objectStore = dbEnq.createObjectStore("admins", { keyPath: "id" });
//     }
// };

// requestDB.onsuccess = function (event) {
//     dbEnq = event.target.result;
//     checkAdminLoginStatus();
//     document.getElementById('adminLogin').addEventListener('submit', handleLogin);
// };

// function handleLogin(event) {
//     event.preventDefault();

//     let adminName = document.getElementById("adminName").value.trim();
//     let adminPassword = document.getElementById("adminPassword").value.trim();
//     let admin = null;

//     if (adminName === "raja" && adminPassword === "raja@22") {
//         admin = { username: "raja", label: "Raja" };

//     } else if (adminName === "murugan" && adminPassword === "murugan@22") {
//         admin = { username: "murugan", label: "Murugan" };

//     } else if (adminName === "mani" && adminPassword === "mani@22") {
//         admin = { username: "mani", label: "Mani" };
//     }
//     if (admin) {
//         Swal.fire({
//             icon: "success",
//             title: `Welcome ${admin.label}!`,
//             text: "Login successfully.",
//             confirmButtonColor: "#28a745",
//             confirmButtonText: "Continue"
//         }).then(() => {
//             saveAdminLoginStatus(true, admin.username);
//         });

//     } else {
//         Swal.fire({
//             icon: "error",
//             title: "Login Failed!",
//             text: "Please try again.",
//             confirmButtonColor: "#d33",
//             confirmButtonText: "Retry"
//         });
//     }
// }

// function saveAdminLoginStatus(isLoggedIn, adminName) {

//     let transaction = dbEnq.transaction(["admins"], "readwrite");
//     let objectStore = transaction.objectStore("admins");

//     let getAll = objectStore.getAll();
//     getAll.onsuccess = function () {
//         let admins = getAll.result;
//         admins.forEach(admin => {
//             admin.isAdminLogin = false;
//             objectStore.put(admin);
//         });

//         let adminData = {
//             id: adminName,
//             isAdminLogin: isLoggedIn,
//             name: adminName
//         };
//         let requestDB = objectStore.put(adminData);

//         requestDB.onsuccess = function () {
//            // autoLogoutUser();
//             checkAdminLoginStatus();
//         };
//     };
// }

// function checkAdminLoginStatus() {
//     let transaction = dbEnq.transaction(["admins"], "readonly");
//     let objectStore = transaction.objectStore("admins");

//     let getAll = objectStore.getAll();
//     getAll.onsuccess = function () {
//         let admins = getAll.result;
//         let loggedInAdmin = admins.find(admin => admin.isAdminLogin === true);

//         let adminNameShow = document.getElementById("adminNameShow");
        
//         if (loggedInAdmin) {
//             adminNameShow.innerHTML = `<h3>Admin ${loggedInAdmin.name}</h3>`;
//             document.querySelector(".containerAdmin").classList.add("d-none");
//             document.getElementById("adminLinks").classList.remove("d-none");
//         } else {
//             document.querySelector(".containerAdmin").classList.remove("d-none");
//             document.getElementById("adminLinks").classList.add("d-none");
//         }

//     };
// }
// let logoutBtn = document.getElementById("logoutBtn");
// if (logoutBtn) {
//     logoutBtn.addEventListener("click", function () {
//         let tx = dbEnq.transaction(["admins"], "readwrite");
//         let store = tx.objectStore("admins");

//         let req = store.getAll();

//         req.onsuccess = function () {
//             let admins = req.result;

//             admins.forEach(admin => {
//                 admin.isAdminLogin = false;
//                 store.put(admin);
//             });
//         };

//         tx.oncomplete = function () {
//             Swal.fire({
//                 icon: 'success',
//                 title: 'Logout!',
//                 text: 'Logout successfully.',
//                 confirmButtonColor: '#28a745',
//                 confirmButtonText: 'Continue'
//             }).then(() => {
//                 checkAdminLoginStatus();
//             });
//         };
//     });
// }

// // function autoLogoutUser() {
// //     let tx = loginDB.transaction(["signUpList"], "readwrite");
// //     let store = tx.objectStore("signUpList");

// //     let req = store.getAll();
// //     req.onsuccess = function () {
// //         let users = req.result;
// //         users.forEach(user => {
// //             user.isLogin = false;
// //             store.put(user);
// //         });
// //     };
// // }

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
        sessionStorage.setItem("adminToken", data.token);
        if (sessionStorage.getItem("adminToken")) {
            sessionStorage.removeItem("token");
        }

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
        showName.innerHTML = `<h3>Admin ${admin.adminName}</h3>`;

        loginContainer.classList.add("d-none");
        adminLinks.classList.remove("d-none");
    });
}

document.addEventListener("DOMContentLoaded", () => {
  const logoutBtn = document.getElementById("logoutBtn");
  logoutBtn.addEventListener("click", () => {
    sessionStorage.removeItem("adminToken");
    sessionStorage.removeItem("admin");

    sessionStorage.clear();

    Swal.fire({
      icon: "success",
      title: "Logged Out",
      confirmButtonColor: "#28a745"
    }).then(() => {
      checkAdminLoginStatus();
      window.location.href = "/admin.html";
    });
  });
});
