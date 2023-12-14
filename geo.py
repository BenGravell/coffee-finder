"""Geography functions and classes."""

from __future__ import annotations

import contextlib
import dataclasses
from typing import Any

import overpass  # type: ignore[import-not-found]
import streamlit as st  # type: ignore[import-not-found]
from geopy.exc import GeocoderServiceError  # type: ignore[import-not-found]
from geopy.geocoders import Nominatim  # type: ignore[import-not-found]
from geopy.point import Point  # type: ignore[import-not-found]

import constants
import open_street_map_utils as osm


def create_overpass_api() -> overpass.API:
    """Create an Overpass API object."""
    return overpass.API()


def create_geocoder() -> Nominatim:
    """Create a geocoder object.

    Uses Nominatim as the geocoder.
    """
    return Nominatim(user_agent=constants.NOMINATIM_USER_AGENT)


@dataclasses.dataclass
class PhysicalAddress:
    """Class that represents a physical address with street, city, and state information.

    This class is designed to hold information about a physical address, including the street
    address, city, and state. It provides methods to format the address and generate a string
    representation.

    Attributes
    ----------
        street (str): The street address (number and street name).
        city (str): The city where the address is located.
        state (str): The state where the address is located.

    Methods
    -------
        flatten: Returns a formatted string representation of the address.

    Examples
    --------
        Creating a PhysicalAddress object:
        >>> address = PhysicalAddress("123 Main St", "Sampletown", "CA")

        Getting a formatted address:
        >>> address.flatten()
        '123 Main St, Sampletown, CA'

    """

    street: str
    city: str
    state: str

    def flatten(self) -> str:
        """Return a formatted string representation of the address.

        Returns
        -------
            str: A formatted address string, including street (if available), city, and state.

        Examples
        --------
            >>> address = PhysicalAddress("123 Main St", "Sampletown", "CA")
            >>> address.flatten()
            '123 Main St, Sampletown, CA'
        """
        x = f"{self.city}, {self.state}"
        if self.street:
            x = f"{self.street}, {x}"
        return x

    def __repr__(self) -> str:
        """Return a string representation of the PhysicalAddress object.

        This method returns the same value as the 'flatten' method.

        Returns
        -------
            str: A formatted address string.

        Examples
        --------
            >>> address = PhysicalAddress("123 Main St", "Sampletown", "CA")
            >>> repr(address)
            '123 Main St, Sampletown, CA'
        """
        return self.flatten()


def get_point_by_geocoding(location: PhysicalAddress | str) -> Point:
    """Get geographic coordinates (Point) for a given location.

    This function retrieves geographic coordinates (latitude and longitude) for a specified location
    using a geocoding service.

    Args:
    ----
        location (PhysicalAddress | str): The location to be geocoded. It can be a PhysicalAddress
            object containing street, city, and state information, or a string representing the address.

    Returns:
    -------
        Point: A Point object containing latitude and longitude coordinates.

    Raises:
    ------
        TypeError: If the 'location' argument is not of type PhysicalAddress or str.
        GeocoderServiceError: If the geocoding service fails to retrieve coordinates for the location.

    Example:
    -------
        Using a PhysicalAddress object:
        >>> address = PhysicalAddress("123 Main St", "Sampletown", "CA")
        >>> get_point_by_geocoding(address)

        Using a string address:
        >>> get_point_by_geocoding("456 Elm St, Anycity, NY")

    """

    def get_query() -> dict[str, str] | str:
        """Get the query for the geocoder."""
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
    """Get the address for a given geographic point using reverse geocoding.

    This function retrieves the nearest address for a specified geographic point (latitude and longitude)
    using a reverse geocoding service.

    Args:
    ----
        point (Point): A Point object containing latitude and longitude coordinates.

    Returns:
    -------
        str | None: The address corresponding to the provided point, or None if no address is found.

    Raises:
    ------
        GeocoderServiceError: If the reverse geocoding service fails to retrieve an address for the point.

    Example:
    -------
        >>> coordinates = Point(40.7128, -74.0060)  # Example coordinates for New York City
        >>> get_address_by_reverse_geocoding(coordinates)
        'New York, NY, USA'
    """
    geocoded_location = st.session_state.geolocator.reverse(point)
    if geocoded_location is None:
        raise GeocoderServiceError
    return geocoded_location.address


@dataclasses.dataclass
class Place:
    """Represents a geographical place, with details such as name, address, website, and geographical coordinates.

    Attributes
    ----------
        name (str | None): The name of the place. Default is None.
        address (PhysicalAddress | str | None): The address of the place, which can be a PhysicalAddress object
                                                 or a plain string. Default is None.
        website (str | None): The website URL of the place. Default is None.
        point (Point | None): A Point object representing the geographical coordinates (latitude and longitude)
                              of the place. Default is None.

    Methods
    -------
        flat_address (property): Returns a flattened string representation of the address.
        structured_address (property): Returns the address in a structured PhysicalAddress format if available,
                                       otherwise returns a flattened string address.
        __post_init__: On initialization, attempts to geocode the address to obtain the Point, if not already provided.
        from_open_street_map_element (classmethod): Creates a Place instance from OpenStreetMap element data.
        has_name_and_point: Checks if the place has both a name and a geographical point defined.
        is_denied: Determines if the place's name is in a given deny list.
        as_flat_dict: Returns the place's details in a flat dictionary format.
    """

    name: str | None = None
    address: PhysicalAddress | str | None = None
    website: str | None = None
    point: Point | None = None

    @property
    def flat_address(self) -> str:
        """Flattened string representation of the address.

        If the address is a PhysicalAddress object,
        it is converted to a string format. If the address is already a string or if no address is defined,
        it returns the address as is or an empty string, respectively.
        """
        if isinstance(self.address, PhysicalAddress):
            return self.address.flatten()
        if isinstance(self.address, str):
            return self.address
        return ""

    @property
    def structured_address(self) -> PhysicalAddress | str:
        """Structured PhysicalAddress format, if available.

        If the address is not a PhysicalAddress object, it returns the flattened string representation of the address.
        """
        if isinstance(self.address, PhysicalAddress):
            return self.address
        return self.flat_address

    def __post_init__(self) -> None:
        """Post-initialization method.

        Attempts to geocode the address to obtain the geographical point (latitude
        and longitude) if the point is not already provided. If geocoding fails, the point remains None.
        """
        if self.point is None:
            with contextlib.suppress(GeocoderServiceError):
                self.point = get_point_by_geocoding(self.structured_address)

    @classmethod
    def from_open_street_map_element(cls, *args: Any, **kwargs: Any) -> Place:
        """Class method to create a Place instance from OpenStreetMap element data.

        Args:
        ----
            args (Any): Positional arguments passed to the OpenStreetMap extraction function.
            kwargs (Any): Keyword arguments passed to the OpenStreetMap extraction function.

        Returns:
        -------
            Place: An instance of Place with data extracted from OpenStreetMap.
        """
        name, address, website, point = osm.extract_place_data_from_element(*args, **kwargs)
        point = None if point is None else Point(point)
        return cls(name, address, website, point)

    def has_name_and_point(self) -> bool:
        """Check whether the place has both a name and a geographical point (latitude and longitude) defined.

        Returns
        -------
            bool: True if both name and point are defined, False otherwise.
        """
        return (self.name is not None) and (self.point is not None)

    def is_denied(self, deny_list: list[str]) -> bool:
        """Check whether the place's name is included in a given deny list. Case-insensitive comparison is used.

        Args:
        ----
            deny_list (list[str]): A list of strings representing denied place names.

        Returns:
        -------
            bool: True if the place's name is in the deny list, False otherwise.
        """
        if self.name is None:
            return False
        return any(deny_name.lower() in self.name.lower() for deny_name in deny_list)

    def as_flat_dict(self) -> dict[str, Any]:
        """Convert the place's details into a flat dictionary format.

        This includes the name, address, website, and geographical coordinates (latitude and longitude).

        Returns
        -------
            dict[str, Any]: A dictionary containing the place's details.
        """
        return {
            "name": self.name,
            "address": self.flat_address,
            "website": self.website,
            "latitude": getattr(self.point, "latitude", None),
            "longitude": getattr(self.point, "longitude", None),
        }
