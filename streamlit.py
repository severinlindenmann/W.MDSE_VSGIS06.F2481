import streamlit as st
from data import sharedmobility
from streamlit_folium import st_folium
import folium
import geopandas as gpd
from shapely.geometry import Point, mapping
from shapely.ops import nearest_points
from streamlit_js_eval import get_geolocation
from folium.features import GeoJsonPopup, GeoJsonTooltip, CustomIcon
import branca.colormap as cm

# Set page config
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

# make h4 titel center
title_alignment = """
<style>
h4 {
  text-align: center
}
</style>
"""
st.markdown(title_alignment, unsafe_allow_html=True)


# initialize session states
if "location" not in st.session_state:
    st.session_state["location"] = {"lat": 47.05048, "lng": 8.30635}

if "last_clicked" not in st.session_state:
    st.session_state["last_clicked"] = None

if "zoom" not in st.session_state:
    st.session_state["zoom"] = 15

# create description
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
st.sidebar.divider()

# load data and transform
EPSG_GLOBAL = "EPSG:4326"
EPSG_SWISS = "EPSG:21781"

# available icons
# CUSTOM_ICON_RED = CustomIcon("data/images/nextbike_icon_red.png", icon_size=(40, 40))
# CUSTOM_ICON_BLUE = CustomIcon("data/images/nextbike_icon_blue.png", icon_size=(40, 40))
# CUSTOM_ICON_GREEN = CustomIcon("data/images/nextbike_icon_green.png", icon_size=(40, 40))


# convert to swiss crs
def convert_to_swiss_crs(gdf):
    return gdf.to_crs(crs=EPSG_SWISS)


# convert to global crs
def convert_to_global_crs(gdf):
    return gdf.to_crs(crs=EPSG_GLOBAL)


# create feature collection
def create_feature_collection(data):
    data = convert_to_global_crs(data)
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


# load data and cache it using streamlit cache function
@st.cache_data
def load_data():
    gdf_city_boundary = sharedmobility("city_boundary")
    gdf_city_boundary = gdf_city_boundary.set_crs(crs=EPSG_GLOBAL)

    gdf_districts_and_stations = sharedmobility("districts_and_stations")
    gdf_districts_and_stations = gdf_districts_and_stations.set_crs(crs=EPSG_GLOBAL)

    gdf_rivers = sharedmobility("rivers")
    gdf_rivers = gdf_rivers.set_crs(crs=EPSG_GLOBAL)

    df_unique_stations = sharedmobility("unique_stations", inside_city=True)
    df_unique_stations["geometry"] = [
        Point(lon, lat)
        for lon, lat in zip(df_unique_stations["lon"], df_unique_stations["lat"])
    ]
    gdf_unique_stations = gpd.GeoDataFrame(df_unique_stations, geometry="geometry")
    gdf_unique_stations = gdf_unique_stations.set_crs(crs=EPSG_GLOBAL)

    gdf_city_boundary = convert_to_swiss_crs(gdf_city_boundary)
    gdf_unique_stations = convert_to_swiss_crs(gdf_unique_stations)
    gdf_districts_and_stations = convert_to_swiss_crs(gdf_districts_and_stations)
    gdf_rivers = convert_to_swiss_crs(gdf_rivers)

    return (
        gdf_unique_stations,
        gdf_city_boundary,
        gdf_districts_and_stations,
        gdf_rivers,
    )


gdf_unique_stations, gdf_city_boundary, gdf_districts_and_stations, gdf_rivers = (
    load_data()
)


# create title
st.title("Nextbike Stationen in Luzern - Karte")

# create selection for map
selected = st.multiselect(
    "Wähle die Funktionen aus, die du veewnden möchtest aus der Liste aus, um die Karte zu personalisieren:",
    [
        "Stadtgrenze",
        "Stationen",
        "Station-Umkreis",
        "Nächste-Station",
        "Viertel",
        "Fluss",
        "Station-in-Fluss-Nähe",
    ],
    default=["Fluss", "Stadtgrenze"],
)

# create columns for 4 top metrics
col1, col2, col3, col4 = st.columns(4)

# count stations
with col1:
    st.metric("Anzahl Stationen", gdf_unique_stations.shape[0])

# calculate city size
with col2:
    gdf_city_boundary["area"] = gdf_city_boundary["geometry"].area
    square_kilometers = round(gdf_city_boundary["area"].iloc[0] / 10**6, 2)
    st.metric("Stadtgrösse (in km^2)", square_kilometers)

# calculate river length
with col3:
    gdf_rivers["length"] = gdf_rivers["geometry"].length
    river_length = round(gdf_rivers["length"].sum() / 1000, 2)
    st.metric("Flusslänge (in km) (Kt. LU)", river_length)

# calculate district count
with col4:
    st.metric("Anzahl Viertel", gdf_districts_and_stations.shape[0])

##### Create Map #####
m = folium.Map(location=[47.05048, 8.30635], zoom_start=st.session_state["zoom"])

# add city boundary to map
if "Stadtgrenze" in selected:
    feature_collection = gpd.GeoSeries(
        gdf_city_boundary.to_crs(crs=EPSG_GLOBAL)["geometry"]
    ).__geo_interface__
    folium.GeoJson(
        feature_collection, style_function=lambda x: {"color": "grey", "opacity": 0.8}
    ).add_to(m)

    # count the length of the city boundary
    gdf_city_boundary["length"] = gdf_city_boundary["geometry"].length
    city_length = round(gdf_city_boundary["length"].sum() / 1000, 2)
    st.sidebar.markdown("### Stadtgrenze")
    st.sidebar.metric("Stadtumfang (in km)", city_length)

# add unique stations to map
if "Stationen" in selected:
    df = gdf_unique_stations.copy()

    st.sidebar.markdown("### Stationen")
    st.sidebar.metric("Anzahl Stationen", gdf_unique_stations.shape[0])
    df = convert_to_global_crs(df)
    for idx, row in df.iterrows():
        custom_icon = CustomIcon(
            "data/images/nextbike_icon_blue.png", icon_size=(40, 40)
        )
        folium.Marker(
            location=[row["lat"], row["lon"]],
            icon=custom_icon,
        ).add_to(m)

# add unique stations in circles
if "Station-Umkreis" in selected:
    df = gdf_unique_stations.copy()
    st.sidebar.markdown("### Station-Umkreis")
    slider_value = st.sidebar.slider(
        "Radius in Metern", min_value=100, max_value=500, value=100, step=100
    )

    df["geometry"] = df.geometry.buffer(slider_value)

    # check that circle is within city boundary, else clip it to boundary
    df["geometry"] = df.intersection(gdf_city_boundary.geometry.iloc[0])

    merged_geometry = df["geometry"].unary_union
    total_area = round(merged_geometry.area / 10**6, 2)
    st.sidebar.metric(
        f"Stations-Abdeckung in %", round(total_area / square_kilometers * 100, 2)
    )

    st.sidebar.divider()

    merged_gdf = gpd.GeoDataFrame(geometry=[merged_geometry])
    merged_gdf.set_crs(crs=EPSG_SWISS, inplace=True)
    merged_geojson = convert_to_global_crs(merged_gdf).__geo_interface__
    folium.GeoJson(
        merged_geojson,
        style_function=lambda feature: {
            "fillColor": "#ffff00",
            "color": "black",
            "weight": 2,
            "dashArray": "5, 5",
        },
    ).add_to(m)

# add nearest stations to map
if "Nächste-Station" in selected:
    df = gdf_unique_stations.copy()

    st.sidebar.markdown("### Nächste-Station")
    st.sidebar.write(
        "Wähle ein Standort auf der Karte oder lasse deinen Standort verwenden"
    )
    if st.sidebar.checkbox("Mein Standort verwenden"):
        loc = get_geolocation()
        if loc:
            st.session_state["location"] = {
                "lat": loc["coords"]["latitude"],
                "lng": loc["coords"]["longitude"],
            }
        loc = st.session_state["location"]
    elif st.session_state["last_clicked"] is not None:
        st.session_state["location"] = st.session_state["last_clicked"]
        loc = st.session_state["location"]
    else:
        loc = st.session_state["location"]

    lon, lat = loc["lng"], loc["lat"]
    st.sidebar.write("Dein ausgewählter Standort:")
    st.sidebar.markdown(
        f"Latitude: {lat} <br> Longitude: {lon}", unsafe_allow_html=True
    )
    custom_icon = CustomIcon("data/images/person.png", icon_size=(40, 40))

    # add location to map
    folium.Marker(
        location=[lat, lon],
        popup="Dein Standort",
        icon=custom_icon,
    ).add_to(m)

    point_gdf = gpd.GeoDataFrame([{"id": 1, "geometry": Point(lon, lat)}])

    point_gdf = point_gdf.set_crs(crs=EPSG_GLOBAL)
    point_gdf = convert_to_swiss_crs(point_gdf)
    df = convert_to_swiss_crs(df)
    df["distance"] = df.distance(point_gdf.iloc[0].geometry)

    df = df.sort_values("distance")
    df = df.head(3).reset_index(drop=True)
    df = convert_to_global_crs(df)

    green_location = [lat, lon]

    # For each red marker, add it to the map, and then draw a line to the green marker
    for idx, row in df.iterrows():
        red_location = [row["lat"], row["lon"]]

        if idx == 0:
            custom_icon = CustomIcon(
                "data/images/nextbike_icon_green.png", icon_size=(40, 40)
            )
        else:
            custom_icon = CustomIcon(
                "data/images/nextbike_icon_red.png", icon_size=(40, 40)
            )

        folium.Marker(
            red_location,
            icon=custom_icon,
            popup=row["name"],
        ).add_to(m)

        # Draw a line between the green and red marker
        line = folium.PolyLine(locations=[green_location, red_location], color="red")
        m.add_child(line)

        # Calculate distance - assuming 'distance' column is in meters
        distance_km = row["distance"] / 1000
        distance_text = f"{distance_km*1000:.0f}m"

        # Add a label with the distance
        middle_point = [
            (green_location[0] + red_location[0]) / 2,
            (green_location[1] + red_location[1]) / 2,
        ]
        folium.Marker(
            middle_point,
            icon=folium.DivIcon(
                html=f'<div style="font-family: sans-serif; font-size: 1.2em; font-weight:bold; color: black;">{distance_text}</div>'
            ),
        ).add_to(m)

    st.sidebar.markdown(
        f"Die nächste Station ist **{df.iloc[0]['name']}**  und {round(df.iloc[0]['distance'], 2)} Meter entfernt"
    )

# add districts to map
if "Viertel" in selected:
    df = gdf_districts_and_stations.copy()
    linear = cm.linear.YlGnBu_09.scale(
        df["station_count"].min(), df["station_count"].max()
    )
    m.add_child(linear)

    def style_function(feature):
        station_count = feature["properties"]["station_count"]
        return {
            "fillColor": linear(station_count),
            "color": "black",
            "weight": 0.5,
            "fillOpacity": 0.7,
        }

    df = convert_to_global_crs(df)
    feature_collection = df.__geo_interface__

    highlight_function = lambda x: {"weight": 3, "color": "black"}

    st.sidebar.markdown("### Viertel")
    st.sidebar.metric("Anzahl Viertel", df.shape[0])

    # Add the GeoJSON to the map with coloring
    folium.GeoJson(
        feature_collection,
        style_function=style_function,
        highlight_function=highlight_function,
        tooltip=GeoJsonTooltip(
            fields=["district_name", "station_count"],
            aliases=["District: ", "Station Count: "],
            localize=True,
        ),
        popup=GeoJsonPopup(
            fields=["district_name", "station_count"],
            aliases=["District: ", "Station Count: "],
        ),
    ).add_to(m)

# add rivers to map
if "Fluss" in selected:
    df2 = gdf_rivers.copy()
    df2 = convert_to_global_crs(df2)
    folium.GeoJson(
        df2.__geo_interface__,
        style_function=lambda feature: {
            "color": "blue",
            "weight": 8,
            "opacity": 0.5,
        },
    ).add_to(m)

# add stations close to rivers to map
if "Station-in-Fluss-Nähe" in selected:
    df = gdf_unique_stations.copy()
    df2 = gdf_rivers.copy()
    st.sidebar.markdown("### Flüsse")
    slider_value = st.sidebar.slider(
        "Entferung von Fluss in M",
        min_value=50,
        max_value=250,
        value=50,
        step=50,
        key="slider_fluesse",
    )

    def stations_close_to_river(stations, rivers, max_distance):
        close_stations = []

        for station in stations.geometry:
            # Calculate the nearest point on any river line to the current station
            nearest_points_list = [
                nearest_points(station, river)[1] for river in rivers.geometry
            ]

            # Calculate the distance from the station to each nearest point on the rivers
            distances = [station.distance(point) for point in nearest_points_list]

            # Check if any of these distances are within the max_distance (slider_value)
            if min(distances) <= max_distance:
                close_stations.append(station)

        # Return a new GeoDataFrame containing only the stations close to a river
        return gpd.GeoDataFrame(geometry=close_stations, crs=EPSG_SWISS)

    # Filter stations close to rivers
    close_stations = stations_close_to_river(df, df2, slider_value)

    st.sidebar.metric(
        f"Anzahl Stationen in der Nähe von Flüssen", close_stations.shape[0]
    )

    close_stations = convert_to_global_crs(close_stations)

    folium.GeoJson(
        close_stations.__geo_interface__,
    ).add_to(m)


##### Render Map #####
center = None
if st.session_state["location"]:
    center = st.session_state["location"]

map_data = st_folium(
    m,
    center=center,
    use_container_width=True,
    returned_objects=["last_clicked"],
    key="map",
)

# update map based on zoom or last clicked
if "Nächste-Station" in selected:
    if (
        map_data["last_clicked"]
        and map_data["last_clicked"] != st.session_state["last_clicked"]
    ):
        st.session_state["last_clicked"] = map_data["last_clicked"]
        st.session_state["zoom"] = 16
        st.experimental_rerun()

if "Nächste-Station" not in selected:
    if st.session_state["zoom"] == 16:
        st.session_state["zoom"] = 15
        st.experimental_rerun()


# add footer
st.sidebar.divider()
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
