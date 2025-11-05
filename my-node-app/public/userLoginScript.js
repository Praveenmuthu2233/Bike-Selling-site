let loginDB;
let loginDetails = indexedDB.open("signUpDetailsDB", 1);

loginDetails.onupgradeneeded = function (event) {
    loginDB = event.target.result;
    loginDB.createObjectStore("signUpList", { autoIncrement: true });
};

loginDetails.onsuccess = function (event) {
    loginDB = event.target.result;
    profileOrLogin();
};

window.onload = function() {
    profileOrLogin();
};
function profileOrLogin() {
    let transaction = loginDB.transaction(["signUpList"], "readonly");
    let objectStore = transaction.objectStore("signUpList");
    let request = objectStore.openCursor();
    let foundLogin = false;

    request.onsuccess = function (event) {
        let cursor = event.target.result;
        if (cursor) {
            let user = cursor.value;
            if (user.isLogin) foundLogin = true;
            cursor.continue();
        } else {
            profileView(foundLogin);
        }
    };
}

function profileView(foundLogin) {
    let loginShowEle = document.getElementsByClassName("loginShow")[0];
    let profileShowEle = document.getElementsByClassName("profileShow")[0];

    if (foundLogin) {
        loginShowEle.classList.add('d-none');
        profileShowEle.classList.remove('d-none');
    } else {
        loginShowEle.classList.remove('d-none');
        profileShowEle.classList.add('d-none');
    }
}

document.addEventListener("DOMContentLoaded", function () {

    showLoginForm();

    function showLoginForm() {
        document.getElementById('signUpBox').style.display = 'none';
        document.getElementById('loginBox').style.display = 'block';
        document.getElementById('loginForm').reset();
    }

    document.getElementById('showSignUp').addEventListener('click', function () {
        document.getElementById('loginBox').style.display = 'none';
        document.getElementById('signUpBox').style.display = 'block';
        document.getElementById('signUpForm').reset();
    });

    document.getElementById('showLogin').addEventListener('click', showLoginForm);

});

function clearErrors() {
    document.querySelectorAll(".error").forEach(el => el.textContent = "");
}

function signUpFormSubmit(event) {
    event.preventDefault();
    clearErrors();

    let firstName = document.getElementById("firstName").value.trim();
    let lastName = document.getElementById("lastName").value.trim();
    let mobileNumber = document.getElementById('mobileNumber').value.trim();
    let emailAddress = document.getElementById('email').value.trim();
    let signUpPassword = document.getElementById('signUpPassword').value.trim();
    let confirmPassword = document.getElementById('confirmPassword').value.trim();
    let agreeTerms = document.getElementById('agreeTerms').checked;

    let valid = true;

    if (firstName.length < 2) {
        document.getElementById("firstNameError").textContent = "First name must be at least 2 characters.";
        valid = false;
    }
    if (!/^[0-9]{10}$/.test(mobileNumber)) {
        document.getElementById("mobileError").textContent = "Enter a valid 10-digit mobile number.";
        valid = false;
    }
    if (emailAddress && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailAddress)) {
        document.getElementById("emailError").textContent = "Enter a valid email address.";
        valid = false;
    }
    if (signUpPassword.length < 6) {
        document.getElementById("passwordError").textContent = "Password must be at least 6 characters long.";
        valid = false;
    }
    if (signUpPassword !== confirmPassword) {
        document.getElementById("confirmPasswordError").textContent = "Passwords do not match.";
        valid = false;
    }
    if (!agreeTerms) {
        document.getElementById("termsError").textContent = "You must agree to the terms.";
        valid = false;
    }
    if (!valid) return;

    fetch(`https://bike-selling-site-1.onrender.com/checkMobile/${mobileNumber}`)
        .then(res => res.json())
        .then(data => {
            if (data.exists) {
                document.getElementById("mobileError").textContent = "Mobile already registered. Please Login.";
                return;
            }

            const user = { firstName, lastName, mobileNumber, email: emailAddress, signUpPassword, isLogin: false };

            fetch('https://bike-selling-site-1.onrender.com/addUser', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(user)
            })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        const transaction = loginDB.transaction(["signUpList"], "readwrite");
                        const store = transaction.objectStore("signUpList");

                        let duplicate = false;
                        store.openCursor().onsuccess = function (event) {
                            let cursor = event.target.result;
                            if (cursor) {
                                if (cursor.value.mobileNumber === mobileNumber) {
                                    duplicate = true;
                                }
                                cursor.continue();
                            } else {
                                if (!duplicate) {
                                    store.add(user);
                                    alert("✅ Signup successful");
                                    showLoginForm();
                                } else {
                                    document.getElementById("mobileError").textContent = "Mobile already exists locally";
                                }
                            }
                        };
                    }
                });
                showLoginForm();
    });
}

document.getElementById('signUpForm').addEventListener('submit', signUpFormSubmit);

function loginFormSubmit(event) {
    event.preventDefault();

    let loginMobileNumber = document.getElementById("loginMobileNumber").value.trim();
    let loginPassword = document.getElementById("loginPassword").value.trim();

    fetch('https://bike-selling-site-1.onrender.com/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mobileNumber: loginMobileNumber, signUpPassword: loginPassword })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {

            const transaction = loginDB.transaction(["signUpList"], "readwrite");
            const store = transaction.objectStore("signUpList");

            store.openCursor().onsuccess = function (event) {
                const cursor = event.target.result;
                if (cursor) {
                    let user = cursor.value;
                    user.isLogin = false;
                    cursor.update(user);
                    cursor.continue();
                }
            };

            transaction.oncomplete = function () {
                const tx2 = loginDB.transaction(["signUpList"], "readwrite");
                const store2 = tx2.objectStore("signUpList");
                let updated = false;

                store2.openCursor().onsuccess = function (event) {
                    const cursor = event.target.result;
                    if (cursor) {
                        let user = cursor.value;
                        if (user.mobileNumber === loginMobileNumber) {
                            user.isLogin = true;
                            cursor.update(user);
                            updated = true;
                        }
                        cursor.continue();
                    }
                };

                tx2.oncomplete = function () {
                    if (updated) {
                        console.log("✅ Login status updated in IndexedDB");
                        window.location.href = "index.html";
                    } else {
                        console.log("⚠️ User not found in IndexedDB");
                        const tx3 = loginDB.transaction(["signUpList"], "readwrite");
                        tx3.objectStore("signUpList").add({
                            firstName: data.firstName || "",
                            lastName: data.lastName || "",
                            mobileNumber: loginMobileNumber,
                            email: data.email || "",
                            isLogin: true
                        });
                        tx3.oncomplete = function () {
                            window.location.href = "index.html";
                        };
                    }
                };
            };
        } else {
            alert("❌ Login failed: " + data.message);
        }
    })
    .catch(err => console.error("❌ SQL login error:", err));
}


document.getElementById('loginForm').addEventListener('submit', loginFormSubmit);
showLoginForm();
