
document.getElementById("bikeForm").addEventListener("submit", function (event) {
  event.preventDefault(); 
  const bikeAddingData = {
    //image : document.getElementById("imageUpload").value,
    listingTitle: document.getElementById("listingTitle").value,
    vehicleNumber: document.getElementById("vehicleNum").value,
    sellerName: document.getElementById("sellerName").value,
    mobileNum: document.getElementById("mobileNum").value,
    bikeCondition: document.getElementById("Condition").value,
    bikeType: document.getElementById("Type").value,
    makedFrom: document.getElementById("Make").value,
    bikeModel: document.getElementById("bikeModel").value,
    bikeKms: document.getElementById("BikeKMS").value,
    bikePrice: document.getElementById("BikePrice").value,
    sellingPrice: document.getElementById("BikePrice").value,
    bikeOwner: document.getElementById("bikeOwner").value,
    bikeBuyingYear: document.getElementById("bikeYear").value,
    bikeColor: document.getElementById("bikeColor").value,
    bikeEngineCC: document.getElementById("EngineCC").value,
    driveType: document.getElementById("driveType").value,
    insurance: document.getElementById("Insurance").value,
    horsepower: document.getElementById("Horsepower").value,
    bikeLocation: document.getElementById("Location").value,
    description: document.getElementById("description").value,
    isAccepted: false,
    isSoldout: false
  };
  fetch(window.API.userAddBike, {
  method: "POST",
  headers: {
    "Content-Type": "application/json"
  },
  body: JSON.stringify(bikeAddingData)
})
  .then(response => response.json())
  .then(data => {
    Swal.fire({
        icon: 'success',
        title: 'Bike added!',
        text: 'Bike added successfully.',
        confirmButtonColor: '#28a745',
        confirmButtonText: 'Continue'
     });
    document.getElementById("bikeForm").reset();
  })
  .catch(err => {
    Swal.fire({
        icon: 'error',
        title: "Can't add!",
        text: 'Bike Adding error.',
        confirmButtonColor: '#28a745',
        confirmButtonText: 'Continue'
    })
  });
});
