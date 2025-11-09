const BASE_URL = "https://bike-selling-site-1.onrender.com";

window.API = {
  BASE_URL: BASE_URL,
  userAddBike: `${BASE_URL}/userAddBike`,
  acceptBike: (id) => `${BASE_URL}/bikes/${id}/accept`,
};
window.CONFIG = {
  enquiryStatusList: ["Cold", "Warm", "Hot"],
  paginationItemPerPage : 8,
  enquiriesPerPage: 8 
};
window.gallery_image = [
  {
    url: "https://cdn.bikedekho.com/processedimages/kawasaki/kawasaki-ninja-zx-10r/source/kawasaki-ninja-zx-10r674008194e755.jpg",
    alt: "Kawasaki Ninja ZX-10R"
  },
  {
    url: "https://acko-cms.ackoassets.com/Best_selling_Bikes_In_India_8f877a56c0.png",
    alt: "Best Selling Bikes in India"
  },
  {
    url: "https://m.rediff.com/getahead/2015/oct/14bike2.jpg",
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