from urllib.parse import quote
import requests

import pandas as pd
import geopy.distance
from geopy.geocoders import Nominatim
import folium
import streamlit as st
from streamlit_folium import folium_static

import config


st.set_page_config(page_title="Coffee Finder", page_icon="☕")


@st.cache_data
def convert_df(df):
    return df.to_csv().encode("utf-8")


def get_distance(x, y):
    return geopy.distance.geodesic(x, y).m


@st.cache_data(ttl=config.TTL)
def get_latitude_longitude(city_name):
    geolocator = Nominatim(user_agent="coffee_finder_app")
    location = geolocator.geocode(city_name)

    if location:
        return location.latitude, location.longitude
    else:
        return None, None


@st.cache_data(ttl=config.TTL)
def get_address(coords):
    geolocator = Nominatim(user_agent="coffee_finder_app")
    location = geolocator.reverse(coords)

    if location:
        return location.address
    else:
        return None


def fit_bounds_from_df(m, df):
    sw = df[["latitude", "longitude"]].min().values.tolist()
    ne = df[["latitude", "longitude"]].max().values.tolist()
    m.fit_bounds([sw, ne])


def dict_to_html(dictionary):
    html = "<table>\n"
    for key, value in dictionary.items():
        html += f"<tr><td>{key}</td><td>{value}</td></tr>\n"
    html += "</table>"
    return html


def make_google_maps_directions_link(params):
    base_str = f"https://www.google.com/maps/dir/?api=1"
    params_str = ""
    for param in params:
        params_str += f"&{param[0]}={quote(param[1])}"
    return base_str + params_str


def address2gmaps_directions_link(address, travelmode):
    # https://developers.google.com/maps/documentation/urls/get-started#directions-action
    gmaps_params = [["destination", address], ["travelmode", travelmode]]
    return make_google_maps_directions_link(gmaps_params)


@st.cache_data(ttl=config.TTL)
def query_osm(amenity, radius, location_lat, location_lon):
    query = f"""
    [out:json];
    (
        node["amenity"="{amenity}"](around:{radius},{location_lat},{location_lon});
        way["amenity"="{amenity}"](around:{radius},{location_lat},{location_lon});
        relation["amenity"="{amenity}"](around:{radius},{location_lat},{location_lon});
    );
    out center;
    """
    response = requests.get(config.OVERPASS_URL_BASE, params={"data": query})
    return response.json()


def df_from_query_data(data):
    place_datas = []
    for element in data["elements"]:
        name, address, website, lat, lon = None, None, None, None, None

        if element["type"] == "node":
            if "lat" in element and "lon" in element:
                lat, lon = element["lat"], element["lon"]
        elif element["type"] == "way":
            if "center" in element:
                if "lat" in element["center"] and "lon" in element["center"]:
                    lat, lon = element["center"]["lat"], element["center"]["lon"]

        if "tags" in element:
            tags = element["tags"]
            if "name" in tags:
                name = tags["name"]
            # Try to use address provided by OpenStreetMaps first
            if "addr:street" in tags and "addr:housenumber" in tags:
                street = tags["addr:street"]
                housenumber = tags["addr:housenumber"]
                address = f"{housenumber} {street}"
            else:
                # Fall back to reverse geocoding by lat/lon if necessary
                address = get_address((lat, lon))
            if "website" in tags:
                website = tags["website"]

        if not any([val is None for val in [name, lat, lon]]):
            place_data = {"name": name, "address": address, "website": website, "latitude": lat, "longitude": lon}
            place_datas.append(place_data)

    if not place_datas:
        st.error("No matches found!")
        return None

    df = pd.DataFrame(place_datas)
    return df


def process_df_from_options(df, deny_list, location_latlon):
    df["valid"] = df.name.apply(lambda x: not any(deny_name.lower() in x.lower() for deny_name in deny_list))
    df = df[df["valid"]]

    # Add distance column
    df["distance (km)"] = df.apply(
        lambda row: round(get_distance((row.latitude, row.longitude), location_latlon) / 1000, 2), axis=1
    )

    df = df.sort_values("distance (km)")
    return df


def generate_map(df, amenity, location, location_latlon, radius, travelmode):
    # Folium map
    m = folium.Map(location=location_latlon, zoom_start=3, control_scale=True)

    fit_bounds_from_df(m, df)

    # Loop through each row in the dataframe
    for i, row in df.iterrows():
        if row["address"] is None:
            google_maps_html = f'(no address available, try a Google search for "{row["name"]} ({row["latitude"]}, {row["longitude"]})")'
        else:
            google_maps_html = f'<a href={address2gmaps_directions_link(row["address"], travelmode)} target="_blank" rel="noopener noreferrer">{row["name"]}</a>'

        # Add each row to the map
        # icons: https://github.com/lennardv2/Leaflet.awesome-markers/blob/2.0/develop/examples/basic-example.html
        color = "green"
        icon = "coffee" if amenity == "cafe" else "cube"
        folium.Marker(
            location=[row["latitude"], row["longitude"]],
            icon=folium.Icon(color=color, icon=icon, prefix="fa"),
            popup=google_maps_html,
            tooltip=f"{row['name']} (Click for Google Maps directions)",
        ).add_to(m)

    folium.Marker(
        location_latlon, tooltip=location, icon=folium.Icon(color="lightgray", icon="home", prefix="fa")
    ).add_to(m)

    # Show disk representing the search area
    folium.Circle(
        location=location_latlon, radius=radius, color="grey", opacity=0.5, dash_array="10", fill=True, fill_opacity=0.2
    ).add_to(m)

    folium_static(m)


def main():
    # Options
    with st.sidebar:
        with st.form("options_form"):
            amenity = st.text_input(
                label="Amenity", value="cafe", help="See https://wiki.openstreetmap.org/wiki/Key:amenity for details."
            )
            location = st.text_input(label="Location", value="Boston, MA", help="Use a city name or address.")
            radius_km = st.number_input(label="Search Radius (km)", min_value=0.0, max_value=10.0, value=2.0, step=0.1, format="%.1f")
            deny_list = st.multiselect("Exclude Tags", ["Starbucks", "Dunkin"], ["Starbucks", "Dunkin"])
            travelmode = st.selectbox("Travel Mode for Google Maps directions", options=["walking", "driving"])
            st.form_submit_button("Submit Search")

    radius = int(radius_km * 1000)
    location_latlon = get_latitude_longitude(location)
    location_lat, location_lon = location_latlon

    if location_lat is None or location_lon is None:
        st.error("Unable to find Location, please try a different search.")
        return None

    # Query OpenStreetMaps to get place data & process it
    data = query_osm(amenity, radius, location_lat, location_lon)
    df = df_from_query_data(data)
    df = process_df_from_options(df, deny_list, location_latlon)
    df = df.reset_index(drop=True)

    # Show an interactive map
    generate_map(df, amenity, location, location_latlon, radius, travelmode)

    st.write(f"Found {df.shape[0]} matches.")

    # Show a downloadable table
    ddf = df.drop(columns="valid")
    st.dataframe(ddf, use_container_width=True)
    st.download_button(
        label="Download CSV",
        data=convert_df(ddf),
        file_name="results.csv",
    )


if __name__ == "__main__":
    main()
