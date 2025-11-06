const BASE_URL = "https://bike-selling-site-1.onrender.com";

window.API = {
  BASE_URL: BASE_URL,
  userAddBike: `${BASE_URL}/userAddBike`,
  acceptBike: (id) => `${BASE_URL}/bikes/${id}/accept`,
};
window.CONFIG = {
  enquiryStatusChangw: ["Cold", "Warm", "Hot"]
};

window.VALIDATION = {
  firstNameMin: 2,
  mobileRegex: /^[0-9]{10}$/,
  emailRegex: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  passwordMin: 6,
  MESSAGES: {
    firstName: "First name must be at least 2 characters.",
    mobile: "Enter a valid 10-digit mobile number.",
    email: "Enter a valid email address.",
    password: "Password must be at least 6 characters long.",
    confirmPassword: "Passwords do not match.",
    terms: "You must agree to the terms."
  }
};
window.ADMIN_CREDENTIALS = [
  { username: "raja", password: "raja@22", label: "Raja" },
  { username: "murugan", password: "murugan@22", label: "Murugan" },
  { username: "mani", password: "mani@22", label: "Mani" }
];
