
import streamlit as st
import folium
from folium.plugins import HeatMap
import random
from geopy.distance import geodesic
from streamlit_folium import st_folium

# Einfache Mapping-Tabelle für PLZ -> Koordinaten
PLZ_COORDS = {
    "10115": (52.532, 13.384),  # Berlin Mitte
    "20095": (53.550, 10.000),  # Hamburg
    "80331": (48.137, 11.575),  # München
    "45127": (51.455, 7.011),   # Essen
}

def get_coords_from_postcode(postcode):
    return PLZ_COORDS.get(postcode, (52.5200, 13.4050))  # Fallback: Berlin

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
postcode = st.sidebar.text_input("Postleitzahl eingeben", value="10115")  # Beispiel: Berlin
refresh_button = st.sidebar.button("🔄 Daten neu generieren")


# Daten generieren


# Prüfen, ob Button geklickt wurde oder PLZ sich geändert hat
if refresh_button or st.session_state.get("last_postcode") != postcode:
    center_coords = get_coords_from_postcode(postcode)
    st.session_state.routers = generate_simulated_data(center=center_coords, num_points=num_points)
    st.session_state.last_postcode = postcode



# Karte anzeigen
with st.spinner("Karte wird erstellt..."):
    map_obj = create_map(st.session_state.routers)
    st_folium(map_obj, width=700, height=500)

st.success("✅ Karte aktualisiert!")
