from typing import Any

from geopy.point import Point  # type: ignore[import-not-found]
from geopy.exc import GeocoderServiceError  # type: ignore[import-not-found]
import pandas as pd
import streamlit as st  # type: ignore[import-not-found]

import constants
import geo


def create_query(amenity: str, radius: float, point: Point, max_results: int) -> str:
    # Define the common query string components
    amenity_str = f'"amenity"="{amenity}"'
    around_str = f"around:{radius},{point.latitude},{point.longitude}"

    # Initialize an empty list to hold each part of the query
    body_lines = []

    # Add each element type (node, way, relation) to the query parts list
    for element in ["node", "way", "relation"]:
        body_lines.append(f"{element}[{amenity_str}]({around_str});")

    # Construct the final query string
    lines = [
        "[out:json];",
        "(",
        *[f"    {body_line}" for body_line in body_lines],
        ");",
        f"out center {constants.OSM_MAX_RESULTS_MULTIPLIER * max_results};",
    ]
    query = "\n".join(lines)

    return query


@st.cache_resource(ttl=constants.TTL)
def query_open_street_map(query: str) -> Any:
    return st.session_state.overpass_api.get(query, responseformat="json", build=False)


def extract_point_from_element(element: dict[str, Any]) -> tuple[float, float]:
    if element["type"] == "node":
        if "lat" in element and "lon" in element:
            return element["lat"], element["lon"]

    if element["type"] == "way":
        if "center" in element:
            if "lat" in element["center"] and "lon" in element["center"]:
                return element["center"]["lat"], element["center"]["lon"]

    raise RuntimeError


def extract_place_data_from_element(
    element: dict[str, Any], attempt_reverse_geocoding: bool
) -> tuple[str | None, str | None, str | None, tuple[float, float] | None,]:
    name = None
    address = None
    website = None
    point = None

    try:
        point = extract_point_from_element(element)
    except RuntimeError:
        pass

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
            if attempt_reverse_geocoding and point is not None:
                try:
                    address = geo.get_address_by_reverse_geocoding(point)
                except GeocoderServiceError:
                    pass

        if "website" in tags:
            website = tags["website"]

    return name, address, website, point


def compute_places_df(
    query_data: Any,
    deny_list: list[str],
    max_results: int,
    attempt_reverse_geocoding: bool,
) -> pd.DataFrame:
    places: list[geo.Place] = []
    num_places = 0
    for element in query_data["elements"]:
        place = geo.Place.from_open_street_map_element(element, attempt_reverse_geocoding)

        if not place.has_name_and_point():
            continue

        if place.is_denied(deny_list):
            continue

        places.append(place)
        num_places += 1

        if num_places >= max_results:
            break

    return pd.DataFrame([place.as_flat_dict() for place in places])
