import dataclasses
from typing import Any

import overpass  # type: ignore[import-not-found]
from geopy.geocoders import Nominatim  # type: ignore[import-not-found]
from geopy.point import Point  # type: ignore[import-not-found]
from geopy.exc import GeocoderServiceError  # type: ignore[import-not-found]
import streamlit as st  # type: ignore[import-not-found]

import constants
import open_street_map_utils as osm


def create_overpass_api() -> overpass.API:
    return overpass.API()


def create_geocoder() -> Nominatim:
    return Nominatim(user_agent=constants.NOMINATIM_USER_AGENT)


@dataclasses.dataclass
class PhysicalAddress:
    street: str
    city: str
    state: str

    def flatten(self) -> str:
        x = f"{self.city}, {self.state}"
        if self.street:
            x = f"{self.street}, {x}"
        return x

    def __repr__(self) -> str:
        return self.flatten()


def get_point_by_geocoding(location: PhysicalAddress | str) -> Point:
    def get_query() -> dict[str, str] | str:
        if isinstance(location, PhysicalAddress):
            return dataclasses.asdict(location)
        if isinstance(location, str):
            return location
        raise TypeError

    geocoded_location = st.session_state.geolocator.geocode(get_query())
    if geocoded_location is None:
        raise GeocoderServiceError

    return geocoded_location.point


def get_address_by_reverse_geocoding(point: Point) -> str | None:
    geocoded_location = st.session_state.geolocator.reverse(point)
    if geocoded_location is None:
        raise GeocoderServiceError
    return geocoded_location.address


@dataclasses.dataclass
class Place:
    name: str | None = None
    address: PhysicalAddress | str | None = None
    website: str | None = None
    point: Point | None = None

    @property
    def flat_address(self) -> str:
        if isinstance(self.address, PhysicalAddress):
            return self.address.flatten()
        if isinstance(self.address, str):
            return self.address
        return ""

    @property
    def structured_address(self) -> PhysicalAddress | str:
        if isinstance(self.address, PhysicalAddress):
            return self.address
        return self.flat_address

    def __post_init__(self) -> None:
        if self.point is None:
            try:
                self.point = get_point_by_geocoding(self.structured_address)
            except GeocoderServiceError:
                pass

    @classmethod
    def from_open_street_map_element(cls, *args: Any, **kwargs: Any) -> "Place":
        name, address, website, point = osm.extract_place_data_from_element(*args, **kwargs)
        point = None if point is None else Point(point)
        return cls(name, address, website, point)

    def has_name_and_point(self) -> bool:
        return (self.name is not None) and (self.point is not None)

    def is_denied(self, deny_list: list[str]) -> bool:
        if self.name is None:
            return False
        return any(deny_name.lower() in self.name.lower() for deny_name in deny_list)

    def as_flat_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "address": self.flat_address,
            "website": self.website,
            "latitude": getattr(self.point, "latitude", None),
            "longitude": getattr(self.point, "longitude", None),
        }
