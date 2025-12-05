let soldOutData = [];
let currentPage = 1;
let itemsPerPage = window.CONFIG.paginationItemPerPage;

function getAdminToken() {
  return sessionStorage.getItem("adminToken");
}

function soldOutPrint() {
  const token = getAdminToken();

  if (!token) {
    Swal.fire({
      icon: "warning",
      title: "Admin Login Required",
      text: "Please login as admin."
    }).then(() => {
      window.location.href = "/my-node-app/public/admin.html";
    });
    return;
  }

  fetch(`${window.API.BASE_URL}/soldout`, {
    method: "GET",
    headers: {
      "Authorization": "Bearer " + token
    }
  })
    .then(res => res.json())
    .then(data => {
      console.log("SOLDOUT RESPONSE:", data);
      soldOutData = Array.isArray(data.data) ? data.data : [];
      currentPage = 1;
      renderSoldOut();
      renderPagination();
    })
    .catch(err => console.error("Error:", err));
}

function getFilteredSoldOutData() {
  const filter = document.getElementById("soldOutFilter")?.value || "all";

  if (filter === "lastweek" || filter === "last30") {
    const now = new Date();
    const days = filter === "lastweek" ? 7 : 30;
    const cutoff = new Date(now.getTime() - days * 24 * 60 * 60 * 1000);

    return soldOutData.filter(bike => {
      if (!bike.soldoutDate) return false;
      const d = new Date(bike.soldoutDate);
      return !isNaN(d) && d >= cutoff;
    });
  }

  return soldOutData;
}


function renderSoldOut() {
  const container = document.getElementById("SoldOut");
  const filteredData = getFilteredSoldOutData();

  if (!filteredData || filteredData.length === 0) {
    container.innerHTML = "<p class='text-center text-muted'>No bikes sold out</p>";
    return;
  }

  const start = (currentPage - 1) * itemsPerPage;
  const end = start + itemsPerPage;
  const pageData = filteredData.slice(start, end);

  let output = "";
  pageData.forEach(bike => {
    const selling = bike.sellingPrice ? Number(bike.sellingPrice) : null;
    const buying = bike.bikePrice ? Number(bike.bikePrice) : null;
    let profitHtml = "";
    if (selling != null && buying != null && !isNaN(selling) && !isNaN(buying)) {
      profitHtml = `<h3>Profit : ${selling - buying}</h3>`;
    }

    output += `
      <div class="col-12 col-md-6 col-lg-3">
        <div class="sold-out-card">
          <div class="soldout-badge">SOLD OUT</div>
          <div class="sold-out-badge"><span class="green">BIKE ID ${bike.originalBikeId}</span></div>
          <img src="${bike.image || ""}" class="img-fluid rounded" style="max-height:180px; object-fit:cover;">
          <div class="m-3">
            <h5>Title: ${bike.listingTitle}</h5>
            <p>Vehicle Number: ${bike.vehicleNumber}</p>
            <p>Seller Name: ${bike.sellerName}</p>
            <p>Mobile Number: ${bike.mobileNum}</p>
            <p>Make: ${bike.makedFrom}</p>
            <p>Model: ${bike.bikeModel}</p>
            <p>Kms: ${bike.bikeKms}</p>
            <p>Selling Price: ${bike.sellingPrice}</p>
            ${bike.bikePrice ? `<p>Buying Price: ${bike.bikePrice}</p>` : ``}
            <p>Owner: ${bike.bikeOwner}</p>
            <p>Year: ${bike.bikeBuyingYear}</p>
          </div>
          ${profitHtml}
        </div>
      </div>
    `;
  });
  container.innerHTML = output;
}

function renderPagination() {
  const filteredData = getFilteredSoldOutData();
  const totalPages = Math.ceil(filteredData.length / itemsPerPage);
  const paginationContainer = document.getElementById("pagination");

  if (totalPages <= 1) {
    paginationContainer.innerHTML = "";
    return;
  }

  let start = currentPage - 1;
  let end = currentPage + 1;

  if (start < 1) {
    start = 1;
    end = Math.min(3, totalPages);
  }

  if (end > totalPages) {
    end = totalPages;
    start = Math.max(1, totalPages - 2);
  }

  let buttons = "";
  buttons += `<button class="btn btn-dark me-2" ${currentPage === 1 ? "disabled" : ""} onclick="goToPage(${currentPage - 1})"><</button>`;
  for (let i = start; i <= end; i++) {
    buttons += `<button class="btn ${i === currentPage ? 'btn-primary' : 'btn-outline-primary'} me-1" onclick="goToPage(${i})">${i}</button>`;
  }
  buttons += `<button class="btn btn-dark ms-2" ${currentPage === totalPages ? "disabled" : ""} onclick="goToPage(${currentPage + 1})">></button>`;
  paginationContainer.innerHTML = buttons;
}

function goToPage(page) {
  currentPage = page;
  renderSoldOut();
  renderPagination();
}

function sortSoldOut() {
  let type = document.getElementById("soldOutSort").value;

  if (type === "newest") {
    soldOutData.sort((a, b) => b.originalBikeId - a.originalBikeId);
  }

  if (type === "oldest") {
    soldOutData.sort((a, b) => a.originalBikeId - b.originalBikeId);
  }

  currentPage = 1;
  renderSoldOut();
  renderPagination();
}

function filterSoldOut() {
  currentPage = 1;
  renderSoldOut();
  renderPagination();
}

async function downloadSoldOutSheet() {
  try {
    const token = getAdminToken();
    if (!token) {
      await Swal.fire({
        icon: "warning",
        title: "Admin Login Required",
        text: "Please login as admin.",
        confirmButtonColor: "#28a745"
      });
      window.location.href = "/my-node-app/public/admin.html";
      return;
    }

    const confirmDownload = await Swal.fire({
      title: "Download Sheet?",
      text: "Do you want to download the SoldOut bikes sheet?",
      icon: "question",
      showCancelButton: true,
      confirmButtonText: "Yes, Download",
      cancelButtonText: "Cancel",
      confirmButtonColor: "#3085d6",
      cancelButtonColor: "#d33"
    });

    if (!confirmDownload.isConfirmed) return;

    const response = await fetch(`${window.API.BASE_URL}/soldout`, {
      method: "GET",
      headers: {
        "Authorization": "Bearer " + token
      }
    });

    const result = await response.json();
    const dataArray = Array.isArray(result.data) ? result.data : [];

    if (!dataArray || dataArray.length === 0) {
      Swal.fire("No Data", "No soldout entries found.", "warning");
      return;
    }

    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, "0");
    const day = String(now.getDate()).padStart(2, "0");
    const fileName = `soldOut_${day}-${month}-${year}.csv`;

    const headers = Object.keys(dataArray[0]);
    const csvRows = [];

    csvRows.push(headers.join(","));
    dataArray.forEach(row => {
      const values = headers.map(header => {
        const value = row[header] != null ? String(row[header]).replace(/"/g, '""') : "";
        return `"${value}"`;
      });
      csvRows.push(values.join(","));
    });

    const csvContent = csvRows.join("\n");
    const blob = new Blob([csvContent], { type: "text/csv" });
    const url = window.URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = fileName;
    a.click();

    window.URL.revokeObjectURL(url);

    Swal.fire({
      title: "Downloaded!",
      text: `${fileName} saved successfully.`,
      icon: "success",
      timer: 2000,
      showConfirmButton: false
    });
  } catch (error) {
    console.error("Error downloading soldout data:", error);
    Swal.fire("Error", "Something went wrong while downloading.", "error");
  }
}
