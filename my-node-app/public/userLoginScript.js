function checkLoginStatus() {
    const token = sessionStorage.getItem("token");

    let loginShowEle = document.getElementsByClassName("loginShow")[0];
    let profileShowEle = document.getElementsByClassName("profileShow")[0];

    if (!token) {
        loginShowEle.classList.remove("d-none");
        profileShowEle.classList.add("d-none");
        return;
    }
    fetch(`${window.API.BASE_URL}/profile`, {
        headers: { "Authorization": "Bearer " + token }
    })
    .then(res => {
        if (!res.ok) throw new Error("Invalid token");
        return res.json();
    })
    .then(profile => {
        loginShowEle.classList.add("d-none");
        profileShowEle.classList.remove("d-none");
        const userName = document.getElementById("userName");
        if (userName) userName.innerText = profile.firstName;
    })
    .catch(() => {
        sessionStorage.removeItem("token");

        loginShowEle.classList.remove("d-none");
        profileShowEle.classList.add("d-none");
    });
}
window.onload = checkLoginStatus;

document.addEventListener("DOMContentLoaded", function () {
    window.showLoginForm = function () {
        document.getElementById('signUpBox').style.display = 'none';
        document.getElementById('loginBox').style.display = 'block';
        document.getElementById('loginForm').reset();
    };

    showLoginForm();
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
    let mobileNumber = document.getElementById("mobileNumber").value.trim();
    let emailAddress = document.getElementById("email").value.trim();
    let signUpPassword = document.getElementById("signUpPassword").value.trim();
    let confirmPassword = document.getElementById("confirmPassword").value.trim();
    let agreeTerms = document.getElementById("agreeTerms").checked;

    let valid = true;
    if (firstName.length < window.VALIDATION.firstNameMin) {
        document.getElementById("firstNameError").textContent = window.VALIDATION.MESSAGES.firstName;
        valid = false;
    }

    if (!window.VALIDATION.mobileRegex.test(mobileNumber)) {
        document.getElementById("mobileError").textContent = window.VALIDATION.MESSAGES.mobile;
        valid = false;
    }

    if (emailAddress && !window.VALIDATION.emailRegex.test(emailAddress)) {
        document.getElementById("emailError").textContent = window.VALIDATION.MESSAGES.email;
        valid = false;
    }

    if (signUpPassword.length < window.VALIDATION.passwordMin) {
        document.getElementById("passwordError").textContent = window.VALIDATION.MESSAGES.password;
        valid = false;
    }

    if (signUpPassword !== confirmPassword) {
        document.getElementById("confirmPasswordError").textContent = window.VALIDATION.MESSAGES.confirmPassword;
        valid = false;
    }

    if (!agreeTerms) {
        document.getElementById("termsError").textContent = window.VALIDATION.MESSAGES.terms;
        valid = false;
    }

    if (!valid) return;

    fetch(`${window.API.BASE_URL}/checkMobile/${mobileNumber}`)
    .then(res => res.json())
    .then(result => {
      if (result.exists) {
        Swal.fire({
            icon: 'error',
            title: 'Signup Failed!',
            text: 'This mobile number is already registered.',
            confirmButtonColor: '#d33'
        });
        return;
      }
      
      submitSignup(firstName, lastName, mobileNumber, emailAddress, signUpPassword);
    })
}
function submitSignup(firstName, lastName, mobileNumber, email, password) {
    let user = { firstName, lastName, mobileNumber, email, signUpPassword:password };
    fetch(`${window.API.BASE_URL}/addUser`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(user)
    })
    .then(res => res.json())
    .then(() => {
        Swal.fire({
            icon: 'success',
            title: 'Signup Successful!',
            text: 'Please login to continue.',
            confirmButtonColor: '#28a745'
        });

        showLoginForm();
    });
}

document.getElementById('signUpForm').addEventListener('submit', signUpFormSubmit);

function loginFormSubmit(event) {
    event.preventDefault();

    let loginMobileNumber = document.getElementById("loginMobileNumber").value.trim();
    let loginPassword = document.getElementById("loginPassword").value.trim();

    fetch(`${window.API.BASE_URL}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            mobileNumber: loginMobileNumber,
            signUpPassword: loginPassword
        })
    })
    .then(async (res) => {
        const text = await res.text();
        try {
            return JSON.parse(text);
        } catch {
            console.error("NON-JSON RESPONSE:", text);
            throw new Error("Server returned invalid JSON");
        }
    })
    .then(data => {
        if (data.success) {
            sessionStorage.setItem("token", data.token);

            Swal.fire({
                icon: 'success',
                title: 'Login Successful!',
                text: `Welcome ${data.user.firstName} ${data.user.lastName}`,
                confirmButtonColor: '#28a745',
            }).then(() => {
                window.location.href = "index.html";
            });

        } else {
            Swal.fire({
                icon: 'error',
                title: 'Login Failed',
                text: data.message,
                confirmButtonColor: '#d33'
            });
        }
    })
    .catch(err => console.error("Login error:", err));
}

// function loginFormSubmit(event) {
//     event.preventDefault();
    
//     let loginMobileNumber = document.getElementById("loginMobileNumber").value.trim();
//     let loginPassword = document.getElementById("loginPassword").value.trim();
    
//     fetch(`${window.API.BASE_URL}/login`, {
//         method: 'POST',
//         headers: { 'Content-Type': 'application/json' },
//         body: JSON.stringify({
//             mobileNumber: loginMobileNumber,
//             signUpPassword: loginPassword
//         })
//     })
//     .then(res => res.json())
//     .then(data => {

//         if (data.success) {
//             sessionStorage.setItem("token", data.token);

//             Swal.fire({
//                 icon: 'success',
//                 title: 'Login Successful!',
//                 text: `Welcome ${data.user.firstName} ${data.user.lastName}`,
//                 confirmButtonColor: '#28a745',
//             }).then(() => {
//                 window.location.href = "index.html";
//             });

//         } else {
//             Swal.fire({
//                 icon: 'error',
//                 title: 'Login Failed',
//                 text: data.message,
//                 confirmButtonColor: '#d33'
//             });
//         }
//     })
//     .catch(err => console.error("Login error:", err));
// }

document.getElementById('loginForm').addEventListener('submit', loginFormSubmit);

function fetchProfile() {
    const token = sessionStorage.getItem("token");
    if (!token) return;

    fetch(`${window.API.BASE_URL}/profile`, {
        headers: {
            "Authorization": "Bearer " + token
        }
    })
    .then(res => res.json())
    .then(profile => {
        document.querySelector(".loginShow").classList.add("d-none");
        document.querySelector(".profileShow").classList.remove("d-none");
        document.getElementById("userName").innerText = profile.firstName;
    })
    .catch(() => sessionStorage.removeItem("token"));
}
function logout() {
    sessionStorage.removeItem("token");
    window.location.href = "userLogin.html";
}

document.getElementById("rememberMe").addEventListener("change", function () {
    document.getElementById("loginPassword").type = this.checked ? "text" : "password";
});

// function verifyOtp() {
//     let entered = document.getElementById("otpInput").value.trim();
    
//     document.getElementById('signUpForm').reset();
//     document.getElementById('loginBox').style.display = 'block';
//     document.getElementById('signUpBox').style.display = 'none';
// }

// document.getElementById("signUpOtpBtn").onclick = async function () {
//     const mobile = document.getElementById("signUpMobileNumber").value.trim();
//     clearErrors();

//     if (!/^[6-9]\d{9}$/.test(mobile)) {
//         document.getElementById("mobileError").textContent = "Enter valid 10-digit mobile number";
//         return;
//     }

//     const check = await fetch(`${window.API.BASE_URL}/checkMobile/${mobile}`).then(r => r.json());
//     if (check.exists) {
//         Swal.fire({ icon: "warning", title: "Already Registered", text: "Mobile number already exists" });
//         return;
//     }

//     const response = await fetch(`${window.API.BASE_URL}/send-otp`, {
//         method: "POST",
//         headers: { "Content-Type": "application/json" },
//         body: JSON.stringify({ mobile })
//     }).then(r => r.json());

//     if (response.success) {
//         receivedOTP = String(response.otp);

//         const modal = new bootstrap.Modal(document.getElementById("otpModal"));
//         modal.show();
//     } else {
//         Swal.fire({ icon: "error", title: "OTP Error", text: "OTP could not be sent" });
//     }
// };

// document.getElementById("forgotPassword").addEventListener("click", function () {
//     var modal = new bootstrap.Modal(document.getElementById('forgotPasswordModal'));
//     modal.show();
// });
// document.getElementById("resetPasswordBtn").addEventListener("click", function () {

//     let mobile = document.getElementById("forgotMobile").value.trim();
//     let newPass = document.getElementById("newPassword").value.trim();
//     let confirmPass = document.getElementById("confirmNewPassword").value.trim();

//     document.getElementById("forgotMobileError").textContent = "";
//     document.getElementById("newPasswordError").textContent = "";
//     document.getElementById("confirmNewPasswordError").textContent = "";

//     let valid = true;

//     if (!window.VALIDATION.mobileRegex.test(mobile)) {
//         document.getElementById("forgotMobileError").textContent = "Invalid mobile number!";
//         valid = false;
//     }

//     if (newPass.length < window.VALIDATION.passwordMin) {
//         document.getElementById("newPasswordError").textContent = "Password is too short!";
//         valid = false;
//     }

//     if (newPass !== confirmPass) {
//         document.getElementById("confirmNewPasswordError").textContent = "Password does not match!";
//         valid = false;
//     }

//     if (!valid) return;
//     fetch(`${window.API.BASE_URL}/resetPassword`, {
//         method: "update",
//         headers: { "Content-Type": "application/json" },
//         body: JSON.stringify({ mobileNumber: mobile, newPassword: newPass })
//     })
//     .then(res => res.json())
//     .then(data => {

//         if (data.success) {

//             const tx = loginDB.transaction(["signUpList"], "readwrite");
//             const store = tx.objectStore("signUpList");

//             store.openCursor().onsuccess = function (event) {
//                 let cursor = event.target.result;
//                 if (cursor) {
//                     let user = cursor.value;
//                     if (user.mobileNumber === mobile) {
//                         user.signUpPassword = newPass;
//                         cursor.update(user);
//                     }
//                     cursor.continue();
//                 }
//             };

//             Swal.fire({
//                 icon: 'success',
//                 title: 'Password Updated',
//                 text: 'Your password has been changed successfully.',
//             });

//             var modal = bootstrap.Modal.getInstance(document.getElementById('forgotPasswordModal'));
//             modal.hide();

//         } else {
//             Swal.fire({
//                 icon: 'error',
//                 title: 'Failed!',
//                 text: data.message || "User not found!"
//             });
//         }

//     })
//     .catch(err => console.log(err));
// });

// let dbEnq;
// function autoLogoutAdmin() {
//     let tx = dbEnq.transaction(["admins"], "readwrite");
//     let store = tx.objectStore("admins");

//     let req = store.getAll();
//     req.onsuccess = function () {
//         let admins = req.result;
//         admins.forEach(admin => {
//             admin.isAdminLogin = false;
//             store.put(admin);
//         });
//     };
// }
