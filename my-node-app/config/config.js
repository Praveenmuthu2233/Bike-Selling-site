// Dynamic BASE_URL: Automatically uses current origin when running locally or on server
const BASE_URL = window.location.origin.includes('localhost') || window.location.origin.includes('127.0.0.1')
  ? window.location.origin
  : window.location.origin;

window.API = {
  BASE_URL: BASE_URL,
  userAddBike: `${BASE_URL}/api/bikes`,
  acceptBike: (id) => `${BASE_URL}/api/admin/bikes/${id}/approve`,
  rejectBike: (id) => `${BASE_URL}/api/admin/bikes/${id}/reject`,
  priceBike: (id) => `${BASE_URL}/api/admin/bikes/${id}/price`,
  soldoutBike: (id) => `${BASE_URL}/api/admin/bikes/${id}/soldout`,
  enquiries: `${BASE_URL}/api/enquiries`,
  bikes: `${BASE_URL}/api/bikes`,
  categories: `${BASE_URL}/api/categories`,
  contact: `${BASE_URL}/api/contact`,
  auth: {
    google: `${BASE_URL}/api/auth/google`,
    demoGoogle: `${BASE_URL}/api/auth/demo-google`,
    me: `${BASE_URL}/api/auth/me`,
    logout: `${BASE_URL}/api/auth/logout`
  },
  user: {
    profile: `${BASE_URL}/api/users/profile`,
    dashboard: `${BASE_URL}/api/users/dashboard`,
    listings: `${BASE_URL}/api/users/listings`,
    enquiries: `${BASE_URL}/api/users/enquiries`,
    favorites: `${BASE_URL}/api/users/favorites`
  },
  admin: {
    login: `${BASE_URL}/api/admin/login`,
    dashboard: `${BASE_URL}/api/admin/dashboard`,
    users: `${BASE_URL}/api/admin/users`,
    bikes: `${BASE_URL}/api/admin/bikes`,
    enquiries: `${BASE_URL}/api/admin/enquiries`,
    messages: `${BASE_URL}/api/admin/messages`,
    auditLogs: `${BASE_URL}/api/admin/audit-logs`,
    changePassword: `${BASE_URL}/api/admin/change-password`
  }
};

window.CONFIG = {
  enquiryStatusList: ["pending", "in_progress", "completed", "cancelled"],
  legacyEnquiryStatusList: ["Cold", "Warm", "Hot", "Not updated"],
  paginationItemPerPage: 8,
  enquiriesPerPage: 6
};

window.DOWNLOAD_CONFIG = {
  types: {
    excel: "Excel (.xlsx)",
    pdf: "PDF (.pdf)",
    text: "Text (.txt)"
  }
};

window.gallery_image = [
  { url: "/IMG-20251204-WA0049.jpg", alt: "Bike Image" },
  { url: "/IMG-20251204-WA0051.jpg", alt: "Bike Image" },
  { url: "/IMG-20251204-WA0052.jpg", alt: "Bike Image" },
  { url: "/IMG-20251204-WA0053.jpg", alt: "Bike Image" },
  { url: "/IMG-20251204-WA0054.jpg", alt: "Bike Image" },
  { url: "/IMG-20251204-WA0055.jpg", alt: "Bike Image" },
  { url: "/IMG-20251204-WA0056.jpg", alt: "Bike Image" },
  { url: "/IMG-20251204-WA0057.jpg", alt: "Bike Image" },
  { url: "/IMG-20251204-WA0058.jpg", alt: "Bike Image" },
  { url: "/IMG-20251204-WA0059.jpg", alt: "Bike Image" },
  { url: "/IMG-20251204-WA0060.jpg", alt: "Bike Image" },
  { url: "/IMG-20251204-WA0061.jpg", alt: "Bike Image" },
  { url: "/IMG-20251204-WA0062.jpg", alt: "Bike Image" },
  { url: "/IMG-20251204-WA0063.jpg", alt: "Bike Image" },
  { url: "/IMG-20251204-WA0064.jpg", alt: "Bike Image" },
  { url: "/IMG-20251204-WA0065.jpg", alt: "Bike Image" },
  { url: "/IMG-20251204-WA0066.jpg", alt: "Bike Image" }
];

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

window.bike_makes = [
  "Ather", "BMW", "Bajaj", "Hero", "Honda", "Java",
  "KTM", "Revolt", "Royal Enfield", "TVS", "Yamaha", "Yezdi", "Others"
];
