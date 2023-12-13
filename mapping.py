import pandas as pd
import folium  # type: ignore[import-not-found]

import constants
import geo
import google_maps_utils
import html_utils


def fit_bounds_from_df(folium_map: folium.Map, df: pd.DataFrame) -> None:
    sw = df[["latitude", "longitude"]].min().values.tolist()
    ne = df[["latitude", "longitude"]].max().values.tolist()
    folium_map.fit_bounds([sw, ne])


def get_popup(row: pd.Series, travel_mode: str) -> folium.Popup:
    # Header
    if row["website"] is None:
        header_content = row["name"]
    else:
        header_content = html_utils.anchor_wrap(text=row["name"], url=row["website"])
    header = html_utils.tag_wrap(header_content, "strong")

    # Address & Google Maps Directions
    if row["address"] is None:
        address_text = "(no address available)"
        google_maps_destination = f'{row["latitude"]},{row["longitude"]}'
    else:
        address_text = row["address"]
        google_maps_destination = f'{row["name"]}, {row["address"]}'
    address = html_utils.tag_wrap(address_text, "small")
    google_maps_content = html_utils.anchor_wrap(
        text="Google Maps", url=google_maps_utils.get_directions_link(google_maps_destination, travel_mode)
    )
    google_maps = html_utils.tag_wrap(google_maps_content, "small")

    # Distance
    distance = html_utils.tag_wrap(f'({row["distance (km)"]} km away)', "small")

    # Full HTML
    html = f"{header} <br> {address} <br> {google_maps} <br> {distance}"

    return folium.Popup(html, min_width=200, max_width=300)


def get_marker(row: pd.Series, travel_mode: str, amenity: str) -> folium.Marker:
    # icons: https://fontawesome.com/v4/icons/
    # examples: https://github.com/lennardv2/Leaflet.awesome-markers/blob/2.0/develop/examples/basic-example.html
    return folium.Marker(
        location=[row["latitude"], row["longitude"]],
        icon=folium.Icon(
            color="green",
            icon=constants.AMENITY_ICON_DICT[amenity],
            prefix="fa",
        ),
        popup=get_popup(row, travel_mode),
        tooltip=f"{row['name']} (click for details)",
    )


def generate_map(home: geo.Place, df: pd.DataFrame, amenity: str, radius: int, travel_mode: str) -> folium.Map:
    assert home.point is not None
    home_point_tuple = (home.point.latitude, home.point.longitude)

    # Create map, centered on the home place
    folium_map = folium.Map(
        location=home_point_tuple,
        zoom_start=constants.FOLIUM_MAP_DEFAULT_ZOOM_LEVEL,
        control_scale=True,
    )

    # Fit the bounds of the map so all points in the df are shown
    fit_bounds_from_df(folium_map, df)

    # Add a marker for each result row
    for i, row in df.iterrows():
        get_marker(row, travel_mode, amenity).add_to(folium_map)

    # Add a marker for the center location
    folium.Marker(
        home_point_tuple,
        tooltip=home.flat_address,
        icon=folium.Icon(color="lightgray", icon="home", prefix="fa"),
    ).add_to(folium_map)

    # Show a disk representing the search area
    folium.Circle(
        location=home_point_tuple,
        radius=radius,
        color="grey",
        opacity=0.5,
        dash_array="10",
        fill=True,
        fill_opacity=0.2,
    ).add_to(folium_map)

    return folium_map
