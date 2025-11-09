
document.addEventListener("DOMContentLoaded", function () {
    const makeSelect = document.getElementById("makedFrom");
    makeSelect.innerHTML = `<option value="">Select</option>`;
    window.bike_makes.forEach(make => {
        const option = document.createElement("option");
        option.value = make;
        option.textContent = make;
        makeSelect.appendChild(option);
    });
});
document.getElementById("bikeForm").addEventListener("submit", async function (e) {
    e.preventDefault();

    const form = document.getElementById("bikeForm");
    form.action = `${window.API.BASE_URL}/addBike`;
    form.method = "POST";

    const formData = new FormData(form);
    formData.delete("galleryImages[]");
    formData.delete("attachments[]");
    const data = Object.fromEntries(formData.entries());
    data.isAccepted = false;
    data.isSoldout = false;

    console.log(data);

    try {
        const response = await fetch(`${window.API.BASE_URL}/addBike`, {
            method: form.method,
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        Swal.fire({
            icon: "success",
            title: "Bike added!",
            text: "Bike added successfully.",
            confirmButtonColor: "#28a745"
        });

        form.reset();
    } catch (err) {
        Swal.fire({
            icon: "error",
            title: "Server Error",
            text: "Unable to add bike."
        });
    }
});



// window.addEventListener("DOMContentLoaded", function () {
//     const form = document.getElementById("bikeForm");
//     form.action = `${window.API.BASE_URL}/addBike`;
//     form.method = "POST";
// });

// document.getElementById("bikeForm").addEventListener("submit", async function (e) {
//     e.preventDefault();

    // const data = {
    //     listingTitle: listingTitle.value,
    //     vehicleNumber: vehicleNumber.value,
    //     sellerName: sellerName.value,
    //     mobileNum: mobileNum.value,
    //     bikeCondition: bikeCondition.value,
    //     bikeType: bikeType.value,
    //     makedFrom: makedFrom.value,
    //     bikeModel: bikeModel.value,
    //     bikeKms: bikeKms.value,
    //     bikePrice: bikePrice.value,
    //     bikeOwner: bikeOwner.value,
    //     bikeBuyingYear: bikeBuyingYear.value,
    //     bikeColor: bikeColor.value,
    //     bikeEngineCC: bikeEngineCC.value,
    //     driveType: driveType.value,
    //     insurance: insurance.value,
    //     horsepower: horsepower.value,
    //     bikeLocation: bikeLocation.value,
    //     description: description.value,
    //     isAccepted: false,
    //     isSoldout: false
    // };

//     try {
//         const response = await fetch(`${window.API.BASE_URL}/addBike`, {
//             method: "POST",
//             headers: { "Content-Type": "application/json" },
//             body: JSON.stringify(data)
//         });

//         const result = await response.json();

//         Swal.fire({
//             icon: "success",
//             title: "Bike added!",
//             text: "Bike added successfully.",
//             confirmButtonColor: "#28a745"
//         });

//         document.getElementById("bikeForm").reset();

//     } catch (err) {
//         Swal.fire({
//             icon: "error",
//             title: "Server Error",
//             text: "Unable to add bike."
//         });
//     }
// });
// document.getElementById("bikeForm").addEventListener("submit", function (event) {
//   event.preventDefault(); 
//   const bikeAddingData = {
//     listingTitle: document.getElementById("listingTitle").value,
//     vehicleNumber: document.getElementById("vehicleNumber").value,
//     sellerName: document.getElementById("sellerName").value,
//     mobileNum: document.getElementById("mobileNum").value,
//     bikeCondition: document.getElementById("bikeCondition").value,
//     bikeType: document.getElementById("bikeType").value,
//     makedFrom: document.getElementById("makedFrom").value,
//     bikeModel: document.getElementById("bikeModel").value,
//     bikeKms: document.getElementById("bikeKms").value,
//     bikePrice: document.getElementById("bikePrice").value,
//     sellingPrice: document.getElementById("bikePrice").value,
//     bikeOwner: document.getElementById("bikeOwner").value,
//     bikeBuyingYear: document.getElementById("bikeBuyingYear").value,
//     bikeColor: document.getElementById("bikeColor").value,
//     bikeEngineCC: document.getElementById("bikeEngineCC").value,
//     driveType: document.getElementById("driveType").value,
//     insurance: document.getElementById("insurance").value,
//     horsepower: document.getElementById("horsepower").value,
//     bikeLocation: document.getElementById("bikeLocation").value,
//     description: document.getElementById("description").value,
//     isAccepted: false,
//     isSoldout: false
//   };

//   fetch(window.API.userAddBike, {
//     method: "POST",
//     headers: { "Content-Type": "application/json" },
//     body: JSON.stringify(bikeAddingData)
//   })
//   .then(response => response.json())
//   .then(() => {
//     Swal.fire({
//         icon: 'success',
//         title: 'Bike added!',
//         text: 'Bike added successfully.',
//         confirmButtonColor: '#28a745'
//      });
//     document.getElementById("bikeForm").reset();
//   })
//   .catch(() => {
//     Swal.fire({
//         icon: 'error',
//         title: "Can't add!",
//         text: 'Bike Adding error.',
//         confirmButtonColor: '#28a745'
//     });
//   });
// });
