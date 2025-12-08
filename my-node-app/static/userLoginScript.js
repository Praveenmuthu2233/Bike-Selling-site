function checkLoginStatus() {
    const userToken = sessionStorage.getItem("token");
    const adminToken = sessionStorage.getItem("adminToken");

    let loginShowEle = document.getElementsByClassName("loginShow")[0];
    let profileShowEle = document.getElementsByClassName("profileShow")[0];
    
    if (adminToken) {
        loginShowEle.classList.add("d-none");
        profileShowEle.classList.add("d-none");
        return;
    }
    if (!userToken) {
        loginShowEle.classList.remove("d-none");
        profileShowEle.classList.add("d-none");
        return;
    }
    
    fetch(`${window.API.BASE_URL}/profile`, {
        headers: { "Authorization": "Bearer " + userToken }
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
            if (sessionStorage.getItem("token")) {
                sessionStorage.removeItem("adminToken");
            }

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