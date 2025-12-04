const BASE_URL = "https://bike-selling-site-1.onrender.com";

window.API = {
  BASE_URL: BASE_URL,
  userAddBike: `${BASE_URL}/userAddBike`,
  acceptBike: (id) => `${BASE_URL}/bikes/${id}/accept`,
};
window.CONFIG = {
  enquiryStatusList: ["Cold", "Warm", "Hot"],
  paginationItemPerPage : 8,
  enquiriesPerPage: 4
};
window.DOWNLOAD_CONFIG = { 
  type: "excel"
};

window.gallery_image = [
  {
    url: "/IMG-20251204-WA0049.jpg",
    alt: "Bike Image"
  },
  {
    url: "/IMG-20251204-WA0051.jpg",
    alt: "Bike Image"
  },
  {
    url: "/IMG-20251204-WA0052.jpg",
    alt: "Bike Image"
  },
  {
    url: "/IMG-20251204-WA0053.jpg",
    alt: "Bike Image"
  },
  {
    url: "/IMG-20251204-WA0054.jpg",
    alt: "Bike Image"
  },
  {
    url: "/IMG-20251204-WA0055.jpg",
    alt: "Bike Image"
  }
  ,
  {
    url: "/IMG-20251204-WA0056.jpg",
    alt: "Bike Image"
  },
  {
    url: "/IMG-20251204-WA0057.jpg",
    alt: "Bike Image"
  },
  {
    url: "/IMG-20251204-WA0058.jpg",
    alt: "Bike Image"
  },
  {
    url: "/IMG-20251204-WA0059.jpg",
    alt: "Bike Image"
  },
  {
    url: "/IMG-20251204-WA0060.jpg",
    alt: "Bike Image"
  },
  {
    url: "/IMG-20251204-WA0061.jpg",
    alt: "Bike Image"
  },
  {
    url: "/IMG-20251204-WA0062.jpg",
    alt: "Bike Image"
  },
  {
    url: "/IMG-20251204-WA0063.jpg",
    alt: "Bike Image"
  },
  {
    url: "/IMG-20251204-WA0064.jpg",
    alt: "Bike Image"
  },
  {
    url: "/IMG-20251204-WA0065.jpg",
    alt: "Bike Image"
  },
  {
    url: "/IMG-20251204-WA0066.jpg",
    alt: "Bike Image"
  }
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

window.bike_makes = ["Ather","BMW","Bajaj","Hero","Honda","Java",
  "KTM","Revolt","Royal Enfield","TVS","Yamaha","Yezdi","Others"
];