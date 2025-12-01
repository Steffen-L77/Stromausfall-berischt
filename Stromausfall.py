
import streamlit as st
import folium
from folium.plugins import HeatMap
import requests
import random
from geopy.distance import geodesic
from streamlit_folium import st_folium

# Funktion: PLZ -> Koordinaten via Nominatim API
def get_coords_from_postcode(postcode):
    url = f"https://nominatim.openstreetmap.org/search?postalcode={postcode}&country=Germany&format=json"
    try:
        response = requests.get(url, headers={"User-Agent": "Streamlit-App"})
        if response.status_code == 200 and response.json():
            data = response.json()[0]
            return (float(data["lat"]), float(data["lon"]))
    except Exception as e:
        st.error(f"Fehler bei Geocoding: {e}")
    return (52.5200, 13.4050)  # Fallback: Berlin

# Funktion: Simulierte Router-Daten generieren
def generate_simulated_data(center=(52.5200, 13.4050), num_points=100):
    routers = []
    for _ in range(num_points):
        lat_offset = random.uniform(-0.02, 0.02)  # ca. 2 km Radius
        lon_offset = random.uniform(-0.02, 0.02)
        status = random.choice(["online", "offline"])
        routers.append({"coords": (center[0] + lat_offset, center[1] + lon_offset), "status": status})
    return routers

# Funktion: Karte erstellen
def create_map(routers, center_coord):
    affected_zones = []
    for router in routers:
        nearby = [r for r in routers if geodesic(router["coords"], r["coords"]).meters <= 200]
        offline_count = sum(1 for r in nearby if r["status"] == "offline")
        if offline_count / len(nearby) >= 0.5:
            affected_zones.append(router["coords"])

 
    m = folium.Map(location=center_location, zoom_start=13)

    # Heatmap für Offline-Router
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
st.title("📡 Ausfallkarte für Internet-Provider (PLZ-basiert)")
st.write("Heatmap + Cluster-Analyse (≥50% offline im Umkreis von 200m)")

# Sidebar für Einstellungen
st.sidebar.header("Einstellungen")
postcode = st.sidebar.text_input("Postleitzahl eingeben", value="10115")  # Standard: Berlin
num_points = st.sidebar.slider("Anzahl der Router", 50, 500, 100)
refresh_button = st.sidebar.button("🔄 Karte aktualisieren")

# Daten generieren bei PLZ-Änderung oder Button-Klick
if refresh_button or st.session_state.get("last_postcode") != postcode:
    center_coords = get_coords_from_postcode(postcode)
    st.session_state.routers = generate_simulated_data(center=center_coords, num_points=num_points)
    st.session_state.last_postcode = postcode

# Karte anzeigen
with st.spinner("Karte wird erstellt..."):
    map_obj = create_map(st.session_state.routers, center_coords)
    st_folium(map_obj, width=700, height=500)

st.success(f"✅ Karte für PLZ {postcode} aktualisiert!")
