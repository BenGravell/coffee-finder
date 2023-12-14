"""Data processing functions."""

import pandas as pd
from geopy.distance import geodesic  # type: ignore[import-not-found]
from geopy.point import Point  # type: ignore[import-not-found]

import app_options as ao
import geo
import open_street_map_utils as osm


def convert_df_to_csv(df: pd.DataFrame, encoding: str = "utf-8") -> bytes:
    """Convert a DataFrame to csv bytes."""
    return df.to_csv().encode(encoding)


def add_distance_column(df: pd.DataFrame, point: Point) -> pd.DataFrame:
    """Add a distance column to a DataFrame."""
    df["distance (km)"] = df.apply(
        lambda row: geodesic((row.latitude, row.longitude), point).km,
        axis=1,
    )
    return df


def compute_places_df(options: ao.Options, home: geo.Place) -> pd.DataFrame:
    """Compute a DataFrame of places based on the specified options and a home location.

    This function queries OpenStreetMap with given parameters to find places of interest.
    It then processes this data, calculating distances from the home location, and filters
    and sorts the places based on these distances.

    Args:
    ----
        options (ao.Options): An object containing search parameters such as amenity type,
                              search radius, maximum number of results, a deny list of place names,
                              and a flag for attempting reverse geocoding.
        home (geo.Place): A Place object representing the home location from which distances
                          to other places will be calculated.

    Returns:
    -------
        pd.DataFrame: A DataFrame containing the processed place data. Columns typically include
                      place names, addresses, websites, geographical coordinates, and distances
                      from the home location. If no places are found or if the home location
                      does not have a defined point (geographical coordinates), an empty DataFrame
                      is returned.

    Notes:
    -----
        - The function first checks if the home location has a defined point. If not, it returns
          an empty DataFrame.
        - Places are filtered to be within the specified radius (in kilometers) from the home location.
        - The DataFrame is sorted by the distance from the home location in ascending order.
        - The index of the DataFrame starts from 1 instead of the default 0.
    """
    if home.point is None:
        return pd.DataFrame()

    # Query OpenStreetMaps to get place data & process it
    query = osm.create_query(
        options.amenity,
        options.radius,
        home.point,
        options.max_results,
    )
    query_data = osm.query_open_street_map(query)
    df = osm.compute_places_df(
        query_data,
        options.deny_list,
        options.max_results,
        options.attempt_reverse_geocoding,
    )
    if df.empty:
        return df

    df = add_distance_column(df, home.point)
    df["distance (km)"] = df["distance (km)"].round(2)
    df = df.sort_values("distance (km)")
    df = df[df["distance (km)"] <= options.radius_km]
    df = df.reset_index(drop=True)
    df.index += 1

    return df
