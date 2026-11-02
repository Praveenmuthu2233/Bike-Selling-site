/**
 * Google Authentication Client Script
 * Handles Google Identity Services (GIS), Token Submission, and Session Storage.
 */

document.addEventListener("DOMContentLoaded", function () {
  // Check if user is already logged in
  const existingToken = sessionStorage.getItem("token");
  if (existingToken) {
    verifyExistingSession(existingToken);
  }

  // Initialize Google Identity Services
  initGoogleAuth();
});

function initGoogleAuth() {
  const clientId = window.GOOGLE_CLIENT_ID || "";
  
  if (window.google && window.google.accounts && clientId) {
    try {
      google.accounts.id.initialize({
        client_id: clientId,
        callback: handleGoogleCredentialResponse,
        auto_select: false,
        cancel_on_tap_outside: true
      });

      const btnContainer = document.getElementById("googleSignInBtn");
      if (btnContainer) {
        google.accounts.id.renderButton(btnContainer, {
          theme: "outline",
          size: "large",
          width: "360",
          text: "continue_with",
          shape: "pill"
        });
      }
    } catch (err) {
      console.warn("[Google Auth] GIS initialization note:", err);
    }
  }
}

/**
 * Initiates Google OAuth popup flow
 */
function initiateGoogleLogin() {
  if (window.google && window.google.accounts && window.GOOGLE_CLIENT_ID) {
    google.accounts.id.prompt();
  } else {
    // If Google Client ID not yet populated in production env, guide user or show notification
    Swal.fire({
      title: "Google Sign-In Configuration",
      text: "To use live Google Sign-In, configure GOOGLE_CLIENT_ID in your .env file. For instant local testing, use the Local Testing / Demo Mode buttons below!",
      icon: "info",
      confirmButtonColor: "#10b981",
      confirmButtonText: "Got it"
    });
  }
}

/**
 * Receives JWT credential token from Google Identity Services
 */
async function handleGoogleCredentialResponse(response) {
  if (!response || !response.credential) {
    Swal.fire({
      icon: "error",
      title: "Authentication Error",
      text: "No credential received from Google. Please try again."
    });
    return;
  }

  try {
    Swal.fire({
      title: "Signing In...",
      text: "Verifying Google account with SMR Motors server...",
      allowOutsideClick: false,
      didOpen: () => Swal.showLoading()
    });

    const res = await fetch(`${window.API.BASE_URL}/api/auth/google`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ credential: response.credential })
    });

    const data = await res.json();

    if (data.success && data.token) {
      sessionStorage.setItem("token", data.token);
      sessionStorage.setItem("user", JSON.stringify(data.user));

      Swal.fire({
        icon: "success",
        title: `Welcome, ${data.user.name}!`,
        text: "You have signed in successfully with Google.",
        confirmButtonColor: "#10b981",
        timer: 1800,
        showConfirmButton: false
      }).then(() => {
        window.location.href = "/profile.html";
      });
    } else {
      throw new Error(data.message || "Failed to authenticate with Google.");
    }
  } catch (err) {
    Swal.fire({
      icon: "error",
      title: "Sign-In Failed",
      text: err.message || "Could not complete sign-in. Please try again.",
      confirmButtonColor: "#ef4444"
    });
  }
}

/**
 * Local Developer / Evaluator Instant Sign-In
 */
async function loginDemoUser(email, name, picture) {
  try {
    Swal.fire({
      title: "Signing In...",
      text: `Authenticating as ${name}...`,
      allowOutsideClick: false,
      didOpen: () => Swal.showLoading()
    });

    const res = await fetch(`${window.API.BASE_URL}/api/auth/demo-google`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, name, picture })
    });

    const data = await res.json();

    if (data.success && data.token) {
      sessionStorage.setItem("token", data.token);
      sessionStorage.setItem("user", JSON.stringify(data.user));

      Swal.fire({
        icon: "success",
        title: `Welcome, ${data.user.name}!`,
        text: "Signed in successfully.",
        confirmButtonColor: "#10b981",
        timer: 1500,
        showConfirmButton: false
      }).then(() => {
        window.location.href = "/profile.html";
      });
    } else {
      throw new Error(data.message || "Demo sign in failed");
    }
  } catch (err) {
    Swal.fire({
      icon: "error",
      title: "Sign-In Error",
      text: err.message,
      confirmButtonColor: "#ef4444"
    });
  }
}

/**
 * Verify active session on page load
 */
async function verifyExistingSession(token) {
  try {
    const res = await fetch(`${window.API.BASE_URL}/api/auth/me`, {
      headers: { Authorization: "Bearer " + token }
    });
    if (res.ok) {
      const data = await res.json();
      if (data.success && data.user) {
        // User already logged in, redirect to profile
        // window.location.href = "/profile.html";
      }
    } else {
      sessionStorage.removeItem("token");
      sessionStorage.removeItem("user");
    }
  } catch (e) {
    // Session check error, ignore
  }
}
