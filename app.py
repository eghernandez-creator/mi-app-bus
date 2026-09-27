from flask import Flask, jsonify, render_template_string
import requests
from google.transit import gtfs_realtime_pb2
import os

app = Flask(__name__)

# Leer la clave desde una variable de entorno (seguro)
API_KEY = os.environ.get("MTA_API_KEY", "TU_CLAVE_API_AQUI")

def obtener_autobuses():
    url = f"https://gtfsrt.prod.obanyc.com/vehiclePositions?key={API_KEY}"
    respuesta = requests.get(url)
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(respuesta.content)
    
    autobuses = []
    for entidad in feed.entity:
        if entidad.HasField('vehicle'):
            v = entidad.vehicle
            autobuses.append({
                "id": v.vehicle.id,
                "ruta": v.trip.route_id,
                "lat": v.position.latitude,
                "lon": v.position.longitude
            })
    return autobuses

@app.route("/datos")
def datos():
    return jsonify(obtener_autobuses())

@app.route("/")
def mapa():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Autobuses NYC en tiempo real</title>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>
            body { margin: 0; font-family: Arial, sans-serif; }
            #map { height: 100vh; width: 100%; }
            #info {
                position: absolute; top: 10px; right: 10px; z-index: 1000;
                background: white; padding: 10px; border-radius: 5px;
                box-shadow: 0 0 10px rgba(0,0,0,0.3);
            }
        </style>
    </head>
    <body>
        <div id="info">🚌 <b id="contador">0</b> autobuses activos</div>
        <div id="map"></div>
        <script>
            var map = L.map('map').setView([40.7128, -74.0060], 12);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap'
            }).addTo(map);

            var markers = {};

            function actualizar() {
                fetch('/datos')
                    .then(r => r.json())
                    .then(autobuses => {
                        document.getElementById('contador').innerText = autobuses.length;
                        autobuses.forEach(bus => {
                            var llave = bus.id;
                            if (markers[llave]) {
                                markers[llave].setLatLng([bus.lat, bus.lon]);
                            } else {
                                markers[llave] = L.marker([bus.lat, bus.lon])
                                    .addTo(map)
                                    .bindPopup('Ruta: ' + bus.ruta + '<br>ID: ' + bus.id);
                            }
                        });
                    })
                    .catch(e => console.error('Error:', e));
            }

            actualizar();
            setInterval(actualizar, 15000);
        </script>
    </body>
    </html>
    """
    return render_template_string(html)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
