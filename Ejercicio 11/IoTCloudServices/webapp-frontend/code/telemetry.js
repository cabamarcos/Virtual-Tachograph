const server_address = window.location.origin.replace(/\/$/, "") + ":5005/";
window.onload = loadTelemetryData;

function loadTelemetryData() {
  const queryString = window.location.search;
  const urlParams = new URLSearchParams(queryString);
  const tachograph = urlParams.get('tachograph');

  const params = { tachograph_id: tachograph };
  const address = server_address + "tachographs/telemetry/";

  let container = document.getElementById("telemetry_list");
  let table = document.createElement("table");

  let thead = document.createElement("thead");
  let tr = document.createElement("tr");
  ["Latitud", "Longitud", "GPS Speed", "Speed", "Driver", "Timestamp"].forEach(text => {
    let th = document.createElement("th");
    th.innerText = text;
    tr.appendChild(th);
  });
  thead.appendChild(tr);
  table.appendChild(thead);

  $.getJSON(address, params, function(result) {
    result.forEach(item => {
      let tr = document.createElement("tr");
      ["latitude", "longitude", "gps_speed", "current_speed", "current_driver_id", "time_stamp"].forEach(field => {
        let td = document.createElement("td");
        td.innerText = item[field];
        tr.appendChild(td);
      });
      table.appendChild(tr);
    });
  });

  table.setAttribute("border", "1");
  container.appendChild(table);
}
function closeModal() {
  const modal = document.getElementById("modalTelemetry");
  modal.style.display = "none";
}

