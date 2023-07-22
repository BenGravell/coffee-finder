from urllib.parse import urlencode
import requests

import pandas as pd
import geopy.distance
from geopy.geocoders import Nominatim
import folium
import streamlit as st
from streamlit_folium import st_folium

import config


st.set_page_config(page_title="Coffee Finder", page_icon="☕")


@st.cache_data(ttl=1 * 60 * 60)  # ttl of 1 hour
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


def address2gmaps_directions_link(address, travelmode):
    # https://developers.google.com/maps/documentation/urls/get-started#directions-action
    params = {"destination": address, "travelmode": travelmode}
    return f"https://www.google.com/maps/dir/?api=1&{urlencode(params)}"


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


def df_from_query_data(query_data, deny_list, max_results, attempt_reverse):
    place_datas = []
    num_place_datas = 0
    for element in query_data["elements"]:
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
                if "addr:city" in tags and "addr:state" in tags:
                    city = tags["addr:city"]
                    state = tags["addr:state"]
                    address += f", {city}, {state}"
                    if "addr:postcode" in tags:
                        postcode = tags["addr:postcode"]
                        address += f" {postcode}"
            else:
                # Fall back to reverse geocoding by lat/lon if necessary
                if attempt_reverse:
                    address = get_address((lat, lon))
            if "website" in tags:
                website = tags["website"]

        place_data = {"name": name, "address": address, "website": website, "latitude": lat, "longitude": lon}
        check_none = not any([val is None for val in [name, lat, lon]])
        if not check_none:
            continue
        check_deny = not any(deny_name.lower() in name.lower() for deny_name in deny_list)
        if check_none and check_deny:
            place_datas.append(place_data)
            num_place_datas += 1

        if num_place_datas >= max_results:
            break

    if not place_datas:
        return None

    return pd.DataFrame(place_datas)


def process_df_from_options(df, location_latlon):
    # Add distance column
    df["distance (km)"] = df.apply(
        lambda row: round(get_distance((row.latitude, row.longitude), location_latlon) / 1000, 2), axis=1
    )

    df = df.sort_values("distance (km)")
    return df


def generate_map(df, amenity, location, location_latlon, radius, travelmode):
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

    st_folium(m, use_container_width=True, returned_objects=[])


def main():
    # Options
    with st.sidebar:
        with st.form("options_form"):
            amenity = st.text_input(
                label="Amenity", value="cafe", help="See https://wiki.openstreetmap.org/wiki/Key:amenity for details."
            )
            location = st.text_input(label="Location", value="Boston, MA", help="Use a city name or address.")
            radius_km = st.number_input(
                label="Search Radius (km)", min_value=0.0, max_value=10.0, value=2.0, step=0.1, format="%.1f"
            )
            deny_list = st.multiselect("Exclude Tags", ["Starbucks", "Dunkin"], ["Starbucks", "Dunkin"])
            travelmode = st.selectbox("Travel Mode for Google Maps directions", options=["walking", "driving"])
            max_results = st.number_input(label="Maximum Number of Results", min_value=1, max_value=1000, value=100)
            attempt_reverse = st.checkbox(
                "Attempt Reverse Geocoding for missing address from OpenStreetMaps?", help="May increase run time."
            )
            st.form_submit_button("Submit Search")

    radius = int(radius_km * 1000)
    location_latlon = get_latitude_longitude(location)
    location_lat, location_lon = location_latlon

    if location_lat is None or location_lon is None:
        st.error("Unable to find Location, please try a different search.")
        return None

    # Query OpenStreetMaps to get place data & process it
    query_data = query_osm(amenity, radius, location_lat, location_lon)
    df = df_from_query_data(query_data, deny_list, max_results, attempt_reverse)
    if df is None:
        st.error("No matches found!")
        return

    df = process_df_from_options(df, location_latlon)
    df = df.reset_index(drop=True)
    df.index += 1

    # Show an interactive map
    generate_map(df, amenity, location, location_latlon, radius, travelmode)

    st.metric("Number of Matches", df.shape[0])

    # Show a downloadable table
    st.dataframe(df, use_container_width=True)
    st.download_button(
        label="Download CSV",
        data=convert_df(df),
        file_name="results.csv",
    )


if __name__ == "__main__":
    main()
