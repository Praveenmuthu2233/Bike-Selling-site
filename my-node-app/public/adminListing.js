// let db;

// let request = indexedDB.open("BikeSellingDB", 1);

// request.onupgradeneeded = function (event) {
//   db = event.target.result;
//   let store = db.createObjectStore("bikesForSale", {
//     keyPath: "id",
//     autoIncrement: true
//   });
// };

// request.onsuccess = function (event) {
//   db = event.target.result;
//   console.log("Database opened successfully");
// };

// let bikeForm = document.getElementById("adminAddBikeForm");

// bikeForm && bikeForm.addEventListener("submit", function (event) {
//   event.preventDefault();

//   let sellingBikeDetails = {
//     image: "https://rajaneditz.com/wp-content/uploads/2022/05/Ktm-rcf-2022-png-3.png",
//     listingTitle: document.getElementById("adminAddlistingTitle").value,
//     vehicleNumber: document.getElementById("adminAddvehicleNum").value,
//     sellerName: document.getElementById("adminAddsellerName").value,
//     mobileNum: document.getElementById("adminAddmobileNum").value,
//     bikeCondition: document.getElementById("adminAddCondition").value,
//     bikeType: document.getElementById("adminAddType").value,
//     makedFrom: document.getElementById("adminAddMake").value,
//     bikeModel: document.getElementById("adminAddbikeModel").value,
//     bikeKms: document.getElementById("adminAddBikeKMS").value,
//     bikePrice: document.getElementById("adminAddBikePrice").value,
//     sellingPrice: document.getElementById("adminAddBikeFixingPrice").value,
//     bikeOwner: document.getElementById("adminAddbikeOwner").value,
//     bikeBuyingYear: document.getElementById("adminAddbikeYear").value,
//     bikeColor: document.getElementById("adminAddbikeColor").value,
//     bikeEngineCC: document.getElementById("adminAddEngineCC").value,
//     driveType: document.getElementById("adminAdddriveType").value,
//     insurance: document.getElementById("adminAddInsurance").value,
//     horsepower: document.getElementById("adminAddHorsepower").value,
//     bikeLocation: document.getElementById("adminAddLocation").value,
//     description: document.getElementById("adminAdddescription").value,
//     isAccepted: true,
//     isSoldout: false
//   };

//   let transaction = db.transaction(["bikesForSale"], "readwrite");
//   let store = transaction.objectStore("bikesForSale");
//   let addRequest = store.add(sellingBikeDetails);

//   addRequest.onsuccess = function () {
//     alert("Bike listing stored successfully!");
//     bikeForm.reset();
//   };
// });
// adminListing.js

document.getElementById("adminAddBikeForm").addEventListener("submit", function(e){
    e.preventDefault(); 
    
    const bikeData = {
        image : document.getElementById("adminAddimageUpload").value,
        listingTitle: document.getElementById("adminAddlistingTitle").value,
        vehicleNumber: document.getElementById("adminAddvehicleNum").value,
        sellerName: document.getElementById("adminAddsellerName").value,
        mobileNum: document.getElementById("adminAddmobileNum").value,
        bikeCondition: document.getElementById("adminAddCondition").value,
        bikeType: document.getElementById("adminAddType").value,
        makedFrom: document.getElementById("adminAddMake").value,
        bikeModel: document.getElementById("adminAddbikeModel").value,
        bikeKms: document.getElementById("adminAddBikeKMS").value,
        bikePrice: document.getElementById("adminAddBikePrice").value,
        sellingPrice: document.getElementById("adminAddBikeFixingPrice").value,
        bikeOwner: document.getElementById("adminAddbikeOwner").value,
        bikeBuyingYear: document.getElementById("adminAddbikeYear").value,
        bikeColor: document.getElementById("adminAddbikeColor").value,
        bikeEngineCC: document.getElementById("adminAddEngineCC").value,
        driveType: document.getElementById("adminAdddriveType").value,
        insurance: document.getElementById("adminAddInsurance").value,
        horsepower: document.getElementById("adminAddHorsepower").value,
        bikeLocation: document.getElementById("adminAddLocation").value,
        description: document.getElementById("adminAdddescription").value,
        isAccepted: true,
        isSoldout: false
    };

    fetch("https://bike-selling-site-1.onrender.com/addBike", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(bikeData)
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message || "Bike added successfully!");
        document.getElementById("adminAddBikeForm").reset();
    })
    .catch(err => {
        console.error(err);
        alert("Error adding bike");
    });
});
