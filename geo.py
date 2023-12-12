import dataclasses

from geopy.geocoders import Nominatim  # type: ignore[import-not-found]
from geopy.distance import geodesic  # type: ignore[import-not-found]
import streamlit as st  # type: ignore[import-not-found]

import constants


def create_geocoder() -> Nominatim:
    return Nominatim(user_agent="coffee_finder_app")


def geodesic_distance_meters(x: tuple[float, float], y: tuple[float, float]) -> float:
    return geodesic(x, y).m


@dataclasses.dataclass
class PhysicalAddress:
    street_address: str
    city: str
    state: str

    def __repr__(self) -> str:
        x = f"{self.city}, {self.state}"
        if self.street_address:
            x = f"{self.street_address}, {x}"
        return x


@dataclasses.dataclass
class LatitudeLongitude:
    latitude: float
    longitude: float

    def as_tuple(self) -> tuple[float, float]:
        return (self.latitude, self.longitude)


@st.cache_resource(ttl=constants.TTL)
def get_latitude_longitude(location: str | PhysicalAddress) -> LatitudeLongitude | None:
    if isinstance(location, PhysicalAddress):
        location = repr(location)

    if geocoded_location := st.session_state.geolocator.geocode(location):
        return LatitudeLongitude(geocoded_location.latitude, geocoded_location.longitude)
    else:
        return None


@st.cache_resource(ttl=constants.TTL)
def get_address(coords: tuple[float, float]) -> str | None:
    location = st.session_state.geolocator.reverse(coords)

    if location:
        return location.address
    else:
        return None


@dataclasses.dataclass
class Location:
    physical_address: PhysicalAddress
    latitude_longitude: LatitudeLongitude | None = None

    def __post_init__(self) -> None:
        if self.latitude_longitude is None:
            self.latitude_longitude = get_latitude_longitude(self.physical_address)


@dataclasses.dataclass
class Place:
    name: str | None = None
    address: str | None = None
    website: str | None = None
    latitude: float | None = None
    longitude: float | None = None

    def has_name_and_latlon(self) -> bool:
        return not any([val is None for val in [self.name, self.latitude, self.longitude]])

    def is_denied(self, deny_list: list[str]) -> bool:
        if self.name is None:
            return True
        return any(deny_name.lower() in self.name.lower() for deny_name in deny_list)
