let map;
const server_address = window.location.origin.replace(/\/$/, "") + ":5005/";
let selectedTachograph = null;


window.initMap = initMap;
setInterval(initMap, 30000);  // refrescar mapa cada minuto

async function initMap() {
  const { Map } = await google.maps.importLibrary("maps");
  const { AdvancedMarkerElement, PinElement } = await google.maps.importLibrary("marker");

  const position = { lat: 40.33256, lng: -3.76516 };  // Madrid
  map = new Map(document.getElementById("map"), {
    center: position,
    zoom: 12,
    mapId: "DEMO_MAP_ID"
  });

  const infoWindow = new google.maps.InfoWindow();
  const address = server_address + "tachographs/active/";

  $.getJSON(address, function(result) {
    console.log(result);
    $.each(result, function(index, item) {
      // CORREGIDO: obtener lat/lng de item.Position
      const m_position = {
        lat: item.latitude,
        lng: item.longitude
      };

      const pinTextGlyph = new PinElement({
        glyph: "T",
        glyphColor: "white"
      });

      const marker = new AdvancedMarkerElement({
        map: map,
        position: m_position,
        content: pinTextGlyph.element,
        title: item.tachograph_id,
        gmpClickable: true
      });

      const contentString =
        '<div id="content">' +
        '<h3>' + marker.title + '</h3>' +
        '<div>' +
        '<p><a href="./telemetry.html?tachograph=' + marker.title + '">Telemetría</a></p>' +
        '<p><a href="./events.html?tachograph=' + marker.title + '">Eventos</a></p>' +
        '<p><a href="./configuration.html?tachograph=' + marker.title + '">Configuración</a></p>' +
        '</div>' +
        '</div>';

      marker.addListener("click", ({ domEvent, latLng }) => {
        infoWindow.close();
        infoWindow.setContent(contentString);
        infoWindow.open(marker.map, marker);
      });
    });
  }).fail(function(jqxhr, textStatus, error) {
    console.error("Error fetching tachograph positions:", textStatus, error);
  });
}
function openModal(id) {
    document.getElementById(id).style.display = "block";
  }
  
  function closeModal(id) {
    document.getElementById(id).style.display = "none";
  }
  
  // eventos de botones del sidebar
  document.getElementById("btnTelemetry").addEventListener("click", function() {
    loadTelemetry();
    openModal('modalTelemetry');
  });
  document.getElementById("btnEvents").addEventListener("click", function() {
    loadEvents();
    openModal('modalEvents');
  });
  document.getElementById("btnConfig").addEventListener("click", function() {
    loadConfig();
    openModal('modalConfig');
  });
  
  // Funciones de carga de datos
  function loadTelemetry() {
    const url = server_address + "tachographs/telemetry/?tachograph_id=" + selectedTachograph;
    fetch(url)
      .then(res => res.json())
      .then(data => {
        let html = "<table border='1'><tr><th>Tipo</th><th>Valor</th></tr>";
        data.forEach(d => {
          html += `<tr><td>${d.Type}</td><td>${d.Value}</td></tr>`;
        });
        html += "</table>";
        document.getElementById("telemetryData").innerHTML = html;
      });
  }
  
  function loadEvents() {
    const url = server_address + "tachographs/events/?tachograph_id=" + selectedTachograph;
    fetch(url)
      .then(res => res.json())
      .then(data => {
        let html = "<table border='1'><tr><th>Evento</th><th>Timestamp</th></tr>";
        data.forEach(d => {
          html += `<tr><td>${d.Event}</td><td>${d.Timestamp}</td></tr>`;
        });
        html += "</table>";
        document.getElementById("eventsData").innerHTML = html;
      });
  }
  
  function loadConfig() {
    const url = server_address + "tachographs/configuration/?tachograph_id=" + selectedTachograph;
    fetch(url)
      .then(res => res.json())
      .then(data => {
        let html = "<table border='1'><tr><th>Parametro</th><th>Valor</th></tr>";
        html += `<tr><td>Frecuencia de Muestreo</td><td>${data.sensors_sampling_rate}</td></tr>`;
        html += `<tr><td>Frecuencia de Envío</td><td>${data.telemetry_rate}</td></tr>`;
        html += "</table>";
        document.getElementById("configData").innerHTML = html;
      });
  }
  
