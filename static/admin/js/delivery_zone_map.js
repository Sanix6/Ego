document.addEventListener("DOMContentLoaded", function () {
  const polygonInput = document.getElementById("id_polygon");
  const mapContainer = document.getElementById("zone-map");

  if (!polygonInput || !mapContainer || typeof mapboxgl === "undefined") {
    return;
  }

  mapboxgl.accessToken = window.MAPBOX_TOKEN;

  const centerLon = Number(window.DARKSTORE_LON || 74.576753);
  const centerLat = Number(window.DARKSTORE_LAT || 42.873462);

  const map = new mapboxgl.Map({
    container: "zone-map",
    style: "mapbox://styles/mapbox/streets-v12",
    center: [centerLon, centerLat],
    zoom: 11,
  });

  const draw = new MapboxDraw({
    displayControlsDefault: false,
    controls: {
      polygon: true,
      trash: true,
    },
    defaultMode: "draw_polygon",
  });

  map.addControl(draw);

  function savePolygon() {
    const data = draw.getAll();

    if (data.features.length > 0) {
      const polygonCoords = data.features[0].geometry.coordinates;
      polygonInput.value = JSON.stringify(polygonCoords);
    } else {
      polygonInput.value = "[]";
    }
  }

  map.on("load", function () {
    if (polygonInput.value) {
      try {
        const coords = JSON.parse(polygonInput.value);
        if (coords && coords.length) {
          draw.add({
            type: "Feature",
            properties: {},
            geometry: {
              type: "Polygon",
              coordinates: coords,
            },
          });
        }
      } catch (e) {
        console.error("Polygon parse error:", e);
      }
    }
  });

  map.on("draw.create", savePolygon);
  map.on("draw.update", savePolygon);
  map.on("draw.delete", savePolygon);
});