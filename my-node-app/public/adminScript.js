let dbEnq;
let requestDB = indexedDB.open("adminLoginDataBase", 1);

requestDB.onupgradeneeded = function (event) {
    dbEnq = event.target.result;
    if (!dbEnq.objectStoreNames.contains("admins")) {
        let objectStore = dbEnq.createObjectStore("admins", { keyPath: "id" });
    }
};

requestDB.onsuccess = function (event) {
    dbEnq = event.target.result;
    checkAdminLoginStatus();
    document.getElementById('adminLogin').addEventListener('submit', handleLogin);
};


function handleLogin(event) {
    event.preventDefault();
    let adminName = document.getElementById("adminName").value;
    let adminPassword = document.getElementById("adminPassword").value;

    let admin = window.ADMIN_CREDENTIALS.find(a =>
        a.username === adminName && a.password === adminPassword
    );
    if (admin) {
        Swal.fire({
            icon: 'success',
            title: `Welcome ${admin.label}!`,
            text: 'Login successfully.',
            confirmButtonColor: '#28a745',
            confirmButtonText: 'Continue'
        }).then(() => {
            saveAdminLoginStatus(true, admin.username);
        });
    }else {
        Swal.fire({
            icon: 'error',
            title: 'Login Failed!',
            text: 'Please try again.',
            confirmButtonColor: '#d33',
            confirmButtonText: 'Retry'
        });
    }
}
function saveAdminLoginStatus(isLoggedIn, adminName) {

    let transaction = dbEnq.transaction(["admins"], "readwrite");
    let objectStore = transaction.objectStore("admins");

    let getAll = objectStore.getAll();
    getAll.onsuccess = function () {
        let admins = getAll.result;
        admins.forEach(admin => {
            admin.isAdminLogin = false;
            objectStore.put(admin);
        });

        let adminData = {
            id: adminName,
            isAdminLogin: isLoggedIn,
            name: adminName
        };
        let requestDB = objectStore.put(adminData);

        requestDB.onsuccess = function () {
           // autoLogoutUser();
            checkAdminLoginStatus();
        };
    };
}

function checkAdminLoginStatus() {
    let transaction = dbEnq.transaction(["admins"], "readonly");
    let objectStore = transaction.objectStore("admins");

    let getAll = objectStore.getAll();
    getAll.onsuccess = function () {
        let admins = getAll.result;
        let loggedInAdmin = admins.find(admin => admin.isAdminLogin === true);

        let adminNameShow = document.getElementById("adminNameShow");
        
        if (loggedInAdmin) {
            adminNameShow.innerHTML = `<h3>Admin ${loggedInAdmin.name}</h3>`;
            document.querySelector(".containerAdmin").classList.add("d-none");
            document.getElementById("adminLinks").classList.remove("d-none");
        } else {
            document.querySelector(".containerAdmin").classList.remove("d-none");
            document.getElementById("adminLinks").classList.add("d-none");
        }

    };
}
let logoutBtn = document.getElementById("logoutBtn");
if (logoutBtn) {
    logoutBtn.addEventListener("click", function () {
        let tx = dbEnq.transaction(["admins"], "readwrite");
        let store = tx.objectStore("admins");

        let req = store.getAll();

        req.onsuccess = function () {
            let admins = req.result;

            admins.forEach(admin => {
                admin.isAdminLogin = false;
                store.put(admin);
            });
        };

        tx.oncomplete = function () {
            Swal.fire({
                icon: 'success',
                title: 'Logout!',
                text: 'Logout successfully.',
                confirmButtonColor: '#28a745',
                confirmButtonText: 'Continue'
            }).then(() => {
                checkAdminLoginStatus();
            });
        };
    });
}

// function autoLogoutUser() {
//     let tx = loginDB.transaction(["signUpList"], "readwrite");
//     let store = tx.objectStore("signUpList");

//     let req = store.getAll();
//     req.onsuccess = function () {
//         let users = req.result;
//         users.forEach(user => {
//             user.isLogin = false;
//             store.put(user);
//         });
//     };
// }