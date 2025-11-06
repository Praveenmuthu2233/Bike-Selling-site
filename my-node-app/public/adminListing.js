document.getElementById("adminAddBikeForm").addEventListener("submit", function(e){
    e.preventDefault(); 
    
    const bikeData = {
        //image : document.getElementById("adminAddimageUpload").value,
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

    fetch(`${window.API.BASE_URL}/addBike`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(bikeData)
    })
    .then(response => response.json())
    .then(data => {
        Swal.fire({
            icon: 'success',
            title: 'Bike added!',
            text: 'Bike added successfully.',
            confirmButtonColor: '#28a745',
            confirmButtonText: 'Continue'
        })
        document.getElementById("adminAddBikeForm").reset();
    })
    .catch(err => {
        console.error(err);
        alert("Error adding bike");
        Swal.fire({
            icon: 'error',
            title: "Can't add!",
            text: 'Bike Adding error.',
            confirmButtonColor: '#28a745',
            confirmButtonText: 'Continue'
        })
    });
});
