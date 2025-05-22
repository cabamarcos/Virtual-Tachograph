const server_address = window.location.origin.replace(/\/$/, "") + ":5005/";
window.onload = search_tachograph_configuration;

function search_tachograph_configuration() {
  const queryString = window.location.search;
  const urlParams = new URLSearchParams(queryString);
  const tachograph = urlParams.get('tachograph');

  const params = { tachograph_id: tachograph };
  const address = server_address + "tachographs/configuration/";

  let container = document.getElementById("configuration_viewer");
  let table = document.createElement("table");
  let thead = document.createElement("thead");
  let tr = document.createElement("tr");

  ["Frecuencia de Muestreo", "Frecuencia de Envío"].forEach(text => {
    let th = document.createElement("th");
    th.innerText = text;
    tr.appendChild(th);
  });

  thead.appendChild(tr);
  table.appendChild(thead);

  $.getJSON(address, params, function(result) {
    let tr = document.createElement("tr");
    ["sensors_sampling_rate", "telemetry_rate"].forEach(field => {
      let td = document.createElement("td");
      td.innerText = result[field];
      tr.appendChild(td);
    });
    table.appendChild(tr);
  });

  table.setAttribute("border", "1");
  container.appendChild(table);
}

function update_configuration() {
  const queryString = window.location.search;
  const urlParams = new URLSearchParams(queryString);
  const tachograph = urlParams.get('tachograph');

  const samplingFrequency = document.getElementById("samplingFrequencyInputText").value;
  const sendingFrequency = document.getElementById("sendingFrequencyInputText").value;

  const params = {
    tachograph_id: tachograph,
    sampling: samplingFrequency,
    rate: sendingFrequency
  };

  $.post(server_address + "tachographs/configuration/", params, function(data) {
    console.log(data);
    alert(data.result);
    location.reload();
  });
}
