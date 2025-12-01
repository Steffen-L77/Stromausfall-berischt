
import streamlit as st
import folium
from folium.plugins import HeatMap
import requests
from geopy.distance import geodesic
from streamlit_folium import st_folium
import time

# Provider-URLs
PROVIDERS = {
    "Telekom": "https://downdetector.com/status-map/telekom.json",
    "Vodafone": "https://downdetector.com/status-map/vodafone.json",
    "1und1": "https://downdetector.com/status-map/1und1.json"
}

def fetch_data():
    routers = []
    for provider, url in PROVIDERS.items():
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                for item in data.get("locations", []):
                    lat = item.get("lat")
                    lon = item.get("lng")
                    routers.append({"coords": (lat, lon), "status": "offline", "provider": provider})
            else:
                print(f"Fehler bei {provider}: Status {response.status_code}")
        except Exception as e:
            print(f"Fehler bei {provider}: {e}")
    return routers

def create_map(routers):
    # Cluster-Analyse: 200m Radius, mindestens 50% offline
    affected_zones = []
    for router in routers:
        nearby = [r for r in routers if geodesic(router["coords"], r["coords"]).meters <= 200]
        offline_count = sum(1 for r in nearby if r["status"] == "offline")
        if offline_count / len(nearby) >= 0.5:
            affected_zones.append(router["coords"])

    # Karte erstellen
    center_location = routers[0]["coords"] if routers else (52.5200, 13.4050)
    m = folium.Map(location=center_location, zoom_start=6)

    # Heatmap-Daten
    heat_data = [r["coords"] for r in routers]
    HeatMap(heat_data, radius=15, blur=10, max_zoom=10).add_to(m)

    # Router-Marker mit Provider-Info
    for router in routers:
        popup_text = f"{router['provider']} - {router['status']}"
        folium.CircleMarker(location=router["coords"], radius=4, color="red", fill=True, fill_color="red",
                             popup=popup_text).add_to(m)

    # Ausfall-Zonen
    for zone in affected_zones:
        folium.Circle(location=zone, radius=200, color="orange", fill=True, fill_opacity=0.2).add_to(m)

    # Karte speichern
    m.save("downdetector_live_heatmap.html")
    print("Karte aktualisiert: downdetector_live_heatmap.html")

# Live-Update alle 5 Minuten
while True:
    routers = fetch_data()
    create_map(routers)
    print("Warte 5 Minuten für das nächste Update...")
    time.sleep(300)  # 300 Sekunden = 5 Minuten
