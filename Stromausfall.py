
import streamlit as st
import folium
from folium.plugins import HeatMap
import random
from geopy.distance import geodesic
from streamlit_folium import st_folium

# Funktion zur Generierung von simulierten Router-Daten
def generate_simulated_data(center=(52.5200, 13.4050), num_points=100):
    routers = []
    for _ in range(num_points):
        lat_offset = random.uniform(-0.05, 0.05)  # ca. 5 km Radius
        lon_offset = random.uniform(-0.05, 0.05)
        status = random.choice(["online", "offline"])
        routers.append({"coords": (center[0] + lat_offset, center[1] + lon_offset), "status": status})
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
    m = folium.Map(location=center_location, zoom_start=12)

    # Heatmap-Daten
    heat_data = [r["coords"] for r in routers if r["status"] == "offline"]
    HeatMap(heat_data, radius=15, blur=10, max_zoom=10).add_to(m)

    # Router-Marker
    for router in routers:
        color = "green" if router["status"] == "online" else "red"
        folium.CircleMarker(location=router["coords"], radius=4, color=color, fill=True, fill_color=color).add_to(m)

    # Cluster-Zonen
    for zone in affected_zones:
        folium.Circle(location=zone, radius=200, color="orange", fill=True, fill_opacity=0.2).add_to(m)

    return m

# Streamlit UI
st.title("📡 Simulierte Ausfallkarte für Internet-Provider")
st.write("Heatmap + Cluster-Analyse (≥50% offline im Umkreis von 200m)")

# Sidebar für Einstellungen
st.sidebar.header("Einstellungen")
num_points = st.sidebar.slider("Anzahl der Router", 50, 500, 100)
refresh_button = st.sidebar.button("🔄 Daten neu generieren")

# Daten generieren
if refresh_button or "routers" not in st.session_state:
    st.session_state.routers = generate_simulated_data(num_points=num_points)

# Karte anzeigen
with st.spinner("Karte wird erstellt..."):
    map_obj = create_map(st.session_state.routers)
    st_folium(map_obj, width=700, height=500)

st.success("✅ Karte aktualisiert!")
