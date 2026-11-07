/**
 * Sell Bike Page Script - SMR Motors
 * Handles multi-image selection, preview, and multipart submission to /api/bikes.
 */

let selectedImages = [];

document.addEventListener("DOMContentLoaded", function () {
    const makeSelect = document.getElementById("makedFrom");
    if (makeSelect && window.bike_makes) {
        makeSelect.innerHTML = `<option value="">Select Make</option>`;
        window.bike_makes.forEach(make => {
            const option = document.createElement("option");
            option.value = make;
            option.textContent = make;
            makeSelect.appendChild(option);
        });
    }

    // Pre-fill seller info if logged in
    const token = localStorage.getItem("token") || sessionStorage.getItem("token");
    if (token) {
        fetch(`${window.API.BASE_URL}/api/users/profile`, {
            headers: { Authorization: "Bearer " + token }
        })
        .then(res => res.json())
        .then(data => {
            if (data.success && data.user) {
                const sellerNameInput = document.getElementById("sellerName");
                const mobileNumInput = document.getElementById("mobileNum");
                if (sellerNameInput) {
                    sellerNameInput.value = data.user.name || "";
                    sellerNameInput.readOnly = true;
                    sellerNameInput.style.backgroundColor = "#f3f4f6";
                }
                if (mobileNumInput && !mobileNumInput.value) {
                    mobileNumInput.value = data.user.phone || "";
                }
            }
        })
        .catch(() => {});
    }

    // Gallery upload input handler
    const galleryInput = document.getElementById("galleryUpload");
    if (galleryInput) {
        galleryInput.addEventListener("change", function (e) {
            const files = Array.from(e.target.files);
            selectedImages = files.slice(0, 6);
            renderPreviews();
        });
    }

    const form = document.getElementById("bikeForm");
    if (form) {
        form.addEventListener("submit", handleSellBikeSubmit);
    }
});

function renderPreviews() {
    const previewContainer = document.getElementById("galleryPreview");
    if (!previewContainer) return;
    previewContainer.innerHTML = "";

    selectedImages.forEach((file, index) => {
        const reader = new FileReader();
        reader.onload = function (e) {
            const div = document.createElement("div");
            div.style.cssText = "display:inline-block; position:relative; margin:6px; width:80px; height:80px; border-radius:8px; overflow:hidden; border:1px solid #ccc;";
            div.innerHTML = `
                <img src="${e.target.result}" style="width:100%; height:100%; object-fit:cover;">
                <button type="button" onclick="removeImage(${index})" style="position:absolute; top:2px; right:2px; background:rgba(0,0,0,0.7); color:#fff; border:none; border-radius:50%; width:20px; height:20px; font-size:12px; cursor:pointer;">&times;</button>
            `;
            previewContainer.appendChild(div);
        };
        reader.readAsDataURL(file);
    });
}

function removeImage(index) {
    selectedImages.splice(index, 1);
    renderPreviews();
}

async function handleSellBikeSubmit(e) {
    e.preventDefault();
    const token = localStorage.getItem("token") || sessionStorage.getItem("token");
    if (!token) {
        if (typeof Swal !== "undefined") {
            Swal.fire({
                icon: "warning",
                title: "Sign In Required",
                text: "Please sign in to list your motorcycle. Authenticated accounts ensure your listing is verified.",
                confirmButtonText: "Sign In Now"
            }).then(() => {
                window.location.href = "/login.html?redirect=/bikeSelling.html";
            });
        } else {
            alert("Please sign in to list your motorcycle.");
            window.location.href = "/login.html?redirect=/bikeSelling.html";
        }
        return;
    }
    const submitBtn = document.getElementById("submitSellingBikeDeatils");
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = "Submitting Listing...";
    }

    const formData = new FormData();
    formData.append("title", document.getElementById("listingTitle").value);
    formData.append("vehicle_number", document.getElementById("vehicleNumber").value);
    formData.append("seller_name", document.getElementById("sellerName").value);
    formData.append("mobileNum", document.getElementById("mobileNum").value);
    formData.append("bike_condition", document.getElementById("bikeCondition").value);
    formData.append("brand", document.getElementById("makedFrom").value || document.getElementById("bikeType").value || "Standard");
    formData.append("model", document.getElementById("bikeModel").value);
    formData.append("kilometers_driven", document.getElementById("bikeKms").value);
    formData.append("price", document.getElementById("bikePrice").value);
    formData.append("selling_price", document.getElementById("bikePrice").value);
    formData.append("year", document.getElementById("bikeBuyingYear") ? document.getElementById("bikeBuyingYear").value : "2022");
    formData.append("bike_color", document.getElementById("bikeColor") ? document.getElementById("bikeColor").value : "Black");
    formData.append("engine_cc", document.getElementById("bikeEngineCC") ? document.getElementById("bikeEngineCC").value : "150cc");
    formData.append("insurance", document.getElementById("insurance") ? document.getElementById("insurance").value : "No");
    formData.append("horsepower", document.getElementById("horsepower") ? document.getElementById("horsepower").value : "No");
    formData.append("location", document.getElementById("bikeLocation") ? document.getElementById("bikeLocation").value : "Chennai");
    formData.append("description", document.getElementById("description") ? document.getElementById("description").value : "");

    // Attach selected images
    selectedImages.forEach(file => {
        formData.append("images", file);
    });

    try {
        const response = await fetch(`${window.API.BASE_URL}/api/bikes`, {
            method: "POST",
            headers: {
                ...(token ? { Authorization: "Bearer " + token } : {})
            },
            body: formData
        });

        const result = await response.json();

        if (result.success) {
            Swal.fire({
                icon: "success",
                title: "Listing Submitted!",
                text: "Your bike listing has been submitted for administrator review. You can track its status in your User Dashboard.",
                confirmButtonColor: "#28a745"
            }).then(() => {
                if (token) {
                    window.location.href = "/profile.html#listings";
                } else {
                    window.location.href = "/";
                }
            });
        } else {
            throw new Error(result.message || "Unable to submit bike.");
        }
    } catch (err) {
        Swal.fire({
            icon: "error",
            title: "Submission Error",
            text: err.message
        });
    } finally {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = "Add Listing";
        }
    }
}
