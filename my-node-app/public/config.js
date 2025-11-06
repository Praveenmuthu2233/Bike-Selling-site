const BASE_URL = "https://bike-selling-site-1.onrender.com";

window.API = {
  BASE_URL: BASE_URL,

  userAddBike: `${BASE_URL}/userAddBike`,
  acceptBike: (id) => `${BASE_URL}/bikes/${id}/accept`,
};
window.CONFIG = {
  enquiryStatusChangw: ["Cold", "Warm", "Hot"]
};
