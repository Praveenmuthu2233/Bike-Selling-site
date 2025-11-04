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

    let mainAdminName1 = 'raja', mainAdminPass1 = 'raja@22';
    let mainAdminName2 = 'murugan', mainAdminPass2 = 'murugan@22';
    let addAdminName = 'mani', addAdminPass = 'mani@22';

    if (adminName === mainAdminName1 && adminPassword === mainAdminPass1) {
        alert('Welcome Raja!');
        saveAdminLoginStatus(true, 'raja');
    } else if (adminName === mainAdminName2 && adminPassword === mainAdminPass2) {
        alert('Welcome Murugan!');
        saveAdminLoginStatus(true, 'murugan');
    } else if (adminName === addAdminName && adminPassword === addAdminPass) {
        alert('Welcome Mani!');
        saveAdminLoginStatus(true, 'mani');
    } else {
        alert('Incorrect username or password');
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
            console.log(`Admin ${adminName} login status saved, others logged out.`);
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
        let transaction = dbEnq.transaction(["admins"], "readwrite");
        let objectStore = transaction.objectStore("admins");

        let getAll = objectStore.getAll();
        getAll.onsuccess = function () {
            let admins = getAll.result;
            admins.forEach(admin => {
                admin.isAdminLogin = false;
                objectStore.put(admin);
            });

            transaction.oncomplete = function () {
                checkAdminLoginStatus();
            };
        };
    });
}