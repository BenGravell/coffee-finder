import dataclasses
import requests
from typing import Any

import pandas as pd
import streamlit as st  # type: ignore[import-not-found]

import constants
import geo


@st.cache_resource(ttl=constants.TTL)
def query_open_street_map(amenity: str, radius: float, location: geo.Location) -> Any:
    assert location.latitude_longitude is not None
    amenity_str = f'''"amenity"="{amenity}"'''
    around_str = f"around:{radius},{location.latitude_longitude.latitude},{location.latitude_longitude.longitude}"
    query = f"""
    [out:json];
    (
        node[{amenity_str}]({around_str});
        way[{amenity_str}]({around_str});
        relation[{amenity_str}]({around_str});
    );
    out center;
    """
    response = requests.get(constants.OVERPASS_URL_BASE, params={"data": query})
    return response.json()


def get_coords_from_element(element: dict[str, Any]) -> tuple[float | None, float | None]:
    if element["type"] == "node":
        if "lat" in element and "lon" in element:
            return element["lat"], element["lon"]

    if element["type"] == "way":
        if "center" in element:
            if "lat" in element["center"] and "lon" in element["center"]:
                return element["center"]["lat"], element["center"]["lon"]

    return None, None


def create_place(element: dict[str, Any], attempt_reverse_geocoding: bool) -> geo.Place:
    name = None
    address = None
    website = None

    lat, lon = get_coords_from_element(element)

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
            if attempt_reverse_geocoding:
                address = geo.get_address((lat, lon))

        if "website" in tags:
            website = tags["website"]

    return geo.Place(name, address, website, lat, lon)


def create_places_df(
    query_data: Any, deny_list: list[str], max_results: int, attempt_reverse_geocoding: bool
) -> pd.DataFrame:
    places = []
    num_places = 0
    for element in query_data["elements"]:
        place = create_place(element, attempt_reverse_geocoding)

        if not place.has_name_and_latlon():
            continue

        if place.is_denied(deny_list):
            continue

        places.append(place)
        num_places += 1

        if num_places >= max_results:
            break

    return pd.DataFrame([dataclasses.asdict(place) for place in places])
