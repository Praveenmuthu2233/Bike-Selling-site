document.getElementById("adminBikeForm").addEventListener("submit", async function (e) {
    e.preventDefault();

    const form = document.getElementById("adminBikeForm");

    const formData = new FormData(form);

    formData.set("isAccepted", "1");
    formData.set("isSoldout", "0");

    console.log("Send");

    try {
        const response = await fetch(`${window.API.BASE_URL}/userAddBike`, {
            method: "POST",
            body: formData
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
        console.error(err);
    }
});


// document.addEventListener("DOMContentLoaded", function () {
//     const makeSelect = document.getElementById("adminAddMake");

//     makeSelect.innerHTML = `<option value="">Select</option>`;

//     window.bike_makes.forEach(make => {
//         const option = document.createElement("option");
//         option.value = make;
//         option.textContent = make;
//         makeSelect.appendChild(option);
//     });
// });

// document.getElementById("adminBikeForm").addEventListener("submit", async function (e) {
//     e.preventDefault();

//     const form = document.getElementById("adminBikeForm");
//     // form.action = `${window.API.BASE_URL}/addBike`;
//     // form.method = "POST";

//     const formData = new FormData(form);
//     formData.delete("galleryImages[]");
//     formData.delete("attachments[]");
//     const data = Object.fromEntries(formData.entries());
//     data.listingTitle= document.getElementById("adminAddlistingTitle").value,
//     data.vehicleNumber = document.getElementById("adminAddvehicleNum").value,
//     data.sellerName = document.getElementById("adminAddsellerName").value,
//     data.mobileNum = document.getElementById("adminAddmobileNum").value,
//     data.bikeCondition = document.getElementById("adminAddCondition").value,
//     data.bikeType = document.getElementById("adminAddType").value,
//     data.makedFrom = document.getElementById("adminAddMake").value,
//     data.bikeModel = document.getElementById("adminAddbikeModel").value,
//     data.bikeKms = document.getElementById("adminAddBikeKMS").value,
//     data.bikePrice = document.getElementById("adminAddBikePrice").value,
//     data.sellingPrice = document.getElementById("adminAddBikeFixingPrice").value,
//     data.bikeOwner = document.getElementById("adminAddbikeOwner").value,
//     data.bikeBuyingYear = document.getElementById("adminAddbikeYear").value,
//     data.bikeColor = document.getElementById("adminAddbikeColor").value,
//     data.bikeEngineCC = document.getElementById("adminAddEngineCC").value,
//     data.driveType = document.getElementById("adminAdddriveType").value,
//     data.insurance= document.getElementById("adminAddInsurance").value,
//     data.horsepower = document.getElementById("adminAddHorsepower").value,
//     data.bikeLocation = document.getElementById("adminAddLocation").value,
//     data.description = document.getElementById("adminAdddescription").value,
//     data.isAccepted = true;
//     data.isSoldout = false;

//     console.log(data);

//     try {
//         const response = await fetch(`${window.API.BASE_URL}/userAddBike`, {
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

//         form.reset();
//     } catch (err) {
//         Swal.fire({
//             icon: "error",
//             title: "Server Error",
//             text: "Unable to add bike."
//         });
//     }
// });