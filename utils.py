import pandas as pd

import geo
import open_street_map_utils
import options


def convert_df_to_csv_utf8(df: pd.DataFrame) -> bytes:
    return df.to_csv().encode("utf-8")


def add_distance_column(df: pd.DataFrame, latitude_longitude: geo.LatitudeLongitude) -> pd.DataFrame:
    df["distance (km)"] = df.apply(
        lambda row: round(
            geo.geodesic_distance_meters((row.latitude, row.longitude), latitude_longitude.as_tuple()) / 1000, 2
        ),
        axis=1,
    )
    return df


def compute_location_and_places_df(options: options.Options) -> tuple[geo.Location, pd.DataFrame | None]:
    places_df = None
    location = geo.Location(options.physical_address)

    if location.latitude_longitude is None:
        return location, places_df

    # Query OpenStreetMaps to get place data & process it
    query_data = open_street_map_utils.query_open_street_map(
        options.amenity,
        options.radius,
        location,
    )
    places_df = open_street_map_utils.create_places_df(
        query_data,
        options.deny_list,
        options.max_results,
        options.attempt_reverse_geocoding,
    )
    if places_df is None:
        return location, places_df

    places_df = add_distance_column(places_df, location.latitude_longitude)
    places_df = places_df.sort_values("distance (km)")
    places_df = places_df.reset_index(drop=True)
    places_df.index += 1

    return location, places_df
