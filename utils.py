import pandas as pd
from geopy.point import Point  # type: ignore[import-not-found]
from geopy.distance import geodesic  # type: ignore[import-not-found]

import geo
import open_street_map_utils as osm
import options


def convert_df_to_csv(df: pd.DataFrame, encoding: str = "utf-8") -> bytes:
    return df.to_csv().encode(encoding)


def add_distance_column(df: pd.DataFrame, point: Point) -> pd.DataFrame:
    df["distance (km)"] = df.apply(
        lambda row: geodesic((row.latitude, row.longitude), point).km,
        axis=1,
    )
    return df


def compute_places_df(options: options.Options, home: geo.Place) -> pd.DataFrame:
    if home.point is None:
        return pd.DataFrame()

    # Query OpenStreetMaps to get place data & process it
    query = osm.create_query(
        options.amenity,
        options.radius,
        home.point,
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
    df = df.reset_index(drop=True)
    df.index += 1

    return df
