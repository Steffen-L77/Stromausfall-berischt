
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

# Funktion zum Abrufen der Daten
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
                st.warning(f"Fehler bei {provider}: Status {response.status_code}")
        except Exception as e:
            st.error(f"Fehler bei {provider}: {e}")
    return routers

# Funktion zur Kartenerstellung
def create_map(routers):
    affected_zones = []
    for router in routers:
        nearby = [r for r in routers if geodesic(router["coords"], r["coords"]).meters <= 200]
        offline_count = sum(1 for r in nearby if r["status"] == "offline")
        if offline_count / len(nearby) >= 0.5:
            affected_zones.append(router["coords"])

    center_location = routers[0]["coords"] if routers else (52.5200, 13.4050)
    m = folium.Map(location=center_location, zoom_start=6)

    # Heatmap hinzufügen
    heat_data = [r["coords"] for r in routers]
    HeatMap(heat_data, radius=15, blur=10, max_zoom=10).add_to(m)

    # Router-Marker
    for router in routers:
        popup_text = f"{router['provider']} - {router['status']}"
        folium.CircleMarker(location=router["coords"], radius=4, color="red", fill=True, fill_color="red",
                             popup=popup_text).add_to(m)

    # Cluster-Zonen
    for zone in affected_zones:
        folium.Circle(location=zone, radius=200, color="orange", fill=True, fill_opacity=0.2).add_to(m)

    return m

# Streamlit UI
st.title("📡 Live-Ausfallkarte für Internet-Provider")
st.write("Heatmap + Cluster-Analyse (≥50% offline im Umkreis von 200m)")

# Automatisches Update-Intervall
update_interval = st.slider("Automatisches Update-Intervall (Minuten)", 1, 10, 5)

# Session-State für letzte Aktualisierung
if "last_update" not in st.session_state:
    st.session_state.last_update = 0

# Button für manuelles Refresh
if st.button("🔄 Jetzt aktualisieren"):
    st.session_state.last_update = time.time()

# Prüfen, ob automatisches Update fällig ist
if time.time() - st.session_state.last_update > update_interval * 60:
    st.session_state.last_update = time.time()

# Daten laden und Karte anzeigen
with st.spinner("Daten werden geladen..."):
    routers = fetch_data()
    map_obj = create_map(routers)
    st_folium(map_obj, width=700, height=500)

st.write(f"Letzte Aktualisierung: {time.strftime('%H:%M:%S')}")
