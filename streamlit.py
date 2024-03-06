import streamlit as st
from data import sharedmobility
from streamlit_folium import st_folium
import folium
import geopandas as gpd
from shapely.geometry import Point, mapping

st.set_page_config(
    page_title="Nextbike | Stadt Luzern",
    page_icon="👋",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://severin.io",
        "Report a bug": "https://severin.io",
        "About": "Analytics Tool Nextbike, erstellt von Severin Lindenmann",
    },
)

title_alignment = """
<style>
h4 {
  text-align: center
}
</style>
"""

st.markdown(title_alignment, unsafe_allow_html=True)

st.sidebar.markdown(
    """
# Analyse von Nextbike Daten in der Stadt Luzern
## im Studiengang B.Sc. Mobility, Data Science and Economics der Hochschule Luzern
#### by Severin Lindenmann, Mai 2024
            """
)

st.sidebar.info(
    "Die Analyse wurde mit öffentlich Zugänglichen Daten durchgeführt. Die Quellen dafür sind unten aufgeführt. Weiter Infos findest du im Github Projekt [Github](https://github.com/severinlindenmann/W.MDSE_VSGIS06.F2481)"
)


def create_feature_collection(data):
    feature_collection = {"type": "FeatureCollection", "features": []}
    for idx, row in data.iterrows():
        feature = {
            "type": "Feature",
            "properties": {"name": row["name"]},
            "id": idx,
            "geometry": mapping(row["geometry"]),
        }

        feature_collection["features"].append(feature)

    return feature_collection


# load data and transform
df_unique_stations = sharedmobility("unique_stations", inside_city=True)
df_unique_stations["geometry"] = [
    Point(lon, lat)
    for lon, lat in zip(df_unique_stations["lon"], df_unique_stations["lat"])
]
gdf_unique_stations = gpd.GeoDataFrame(df_unique_stations, geometry="geometry")
gdf_unique_stations = gdf_unique_stations.set_crs(epsg=4326)
gdf_city_boundary = sharedmobility("city_boundary")
gdf_city_boundary = gdf_city_boundary.to_crs(epsg=32633)

st.title("Nextbike Stationen in Luzern - Karte")

selected = st.multiselect(
    "Wähle die Funktionen aus, die du veewnden möchtest aus der Liste aus, um die Karte zu personalisieren:",
    ["Stadtgrenze", "Stationen", "Station-Umkreis"],
    default=["Stadtgrenze", "Station-Umkreis"],
)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Anzahl Stationen", gdf_unique_stations.shape[0])

with col2:
    gdf_city_boundary["area"] = gdf_city_boundary["geometry"].area
    square_kilometers = round(gdf_city_boundary["area"].iloc[0] / 10**6, 2)
    st.metric("Stadtgrösse (in km^2)", square_kilometers)

# create starting map
m = folium.Map(location=[47.05048, 8.30635], zoom_start=15)

if "Stadtgrenze" in selected:
    feature_collection = gpd.GeoSeries(
        gdf_city_boundary.to_crs(epsg=4326)["geometry"]
    ).__geo_interface__
    folium.GeoJson(feature_collection).add_to(m)

# add unique stations to map
if "Stationen" in selected:
    popup = folium.GeoJsonPopup(fields=["name"])
    folium.GeoJson(create_feature_collection(gdf_unique_stations), popup=popup).add_to(
        m
    )

if "Station-Umkreis" in selected:
    st.sidebar.divider()
    st.sidebar.markdown("### Station-Umkreis")
    slider_value = st.sidebar.slider(
        "Radius in Metern", min_value=100, max_value=500, value=100, step=100
    )

    # add unique stations in circles
    gdf_projected = gdf_unique_stations.to_crs(epsg=32633)
    gdf_projected["geometry"] = gdf_projected.geometry.buffer(slider_value)
    gdf_circles = gdf_projected.to_crs(epsg=4326)
    # folium.GeoJson(create_feature_collection(gdf_circles)).add_to(m)

    # check that circle is within city boundary, else clip it to boundary
    gdf_projected["geometry"] = gdf_projected.intersection(
        gdf_city_boundary.geometry.iloc[0]
    )
    # gdf_city_boundary["geometry"]

    merged_geometry = gdf_projected["geometry"].unary_union
    total_area = round(merged_geometry.area / 10**6, 2)
    # col3.metric(f"Abdeckung (km^2) durch Stationen mit Radius {slider_value}m", total_area)
    st.sidebar.metric(
        f"Stations-Abdeckung in %", round(total_area / square_kilometers * 100, 2)
    )

    st.sidebar.divider()

    merged_gdf = gpd.GeoDataFrame(geometry=[merged_geometry], crs=gdf_projected.crs)
    merged_geojson = merged_gdf.to_crs(epsg=4326).__geo_interface__
    folium.GeoJson(
        merged_geojson,
        style_function=lambda feature: {
            "fillColor": "#ffff00",
            "color": "black",
            "weight": 2,
            "dashArray": "5, 5",
        },
    ).add_to(m)

# call to render Folium map in Streamlit
st_data = st_folium(m, use_container_width=True)
st.write(st_data)

st.sidebar.markdown(
    """

   
### Eingesetzte Tools
- [Streamlit](https://www.streamlit.io/)
- [Folium](https://python-visualization.github.io/folium/)
- [Google BigQuery](https://cloud.google.com/bigquery)

### Quellen
- [Nextbike](https://www.nextbike.de/)
- [Shared Mobility](https://github.com/SFOE/sharedmobility)
- [Bevölkerung Luzern](https://www.lustat.ch/)
- [Openstreetmap](https://www.openstreetmap.org/)
"""
)
