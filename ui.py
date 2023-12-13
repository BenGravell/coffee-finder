import pandas as pd
import streamlit as st  # type: ignore[import-not-found]
from streamlit_folium import st_folium  # type: ignore[import-not-found]

import constants
import geo
import options
import utils

import mapping


class TitleSection:
    @staticmethod
    def run() -> None:
        st.title(f"{constants.APP_ICON} {constants.APP_TITLE}", anchor=False)


class OptionsSection:
    @staticmethod
    def get_options_from_ui() -> options.Options:
        default_options = options.Options()

        amenity = st.selectbox(
            label="Amenity",
            options=constants.AMENITY_OPTIONS,
            format_func=lambda x: x.replace("_", " ").title(),
            index=constants.AMENITY_OPTIONS.index(default_options.amenity),
            help="See https://wiki.openstreetmap.org/wiki/Key:amenity for details.",
        )

        street = st.text_input(
            label="Street Address (optional)",
            value=default_options.physical_address.street,
        )
        city = st.text_input(
            label="City",
            value=default_options.physical_address.city,
        )
        state = st.text_input(
            label="State",
            value=default_options.physical_address.state,
            help="Can use full state name or abbreviation.",
        )
        physical_address = geo.PhysicalAddress(
            street,
            city,
            state,
        )

        radius_km = st.number_input(
            label="Search Radius (km)",
            min_value=0.0,
            max_value=100.0,
            value=default_options.radius_km,
            step=0.1,
            format="%.1f",
        )
        deny_list = st.multiselect(
            label="Exclude Tags",
            options=constants.EXCLUDE_TAG_OPTIONS,
            default=default_options.deny_list,
        )
        travel_mode = st.selectbox(
            label="Travel Mode for Google Maps directions",
            options=constants.TRAVEL_MODE_OPTIONS,
            index=constants.TRAVEL_MODE_OPTIONS.index(default_options.travel_mode),
            format_func=lambda x: x.title(),
        )
        max_results = st.number_input(
            label="Maximum Number of Results",
            min_value=1,
            max_value=1000,
            value=default_options.max_results,
        )
        attempt_reverse_geocoding = st.toggle(
            label="Attempt Reverse Geocoding for missing address from OpenStreetMaps?",
            value=default_options.attempt_reverse_geocoding,
            help=(
                "Use latitude and longitude coordinates for reverse geocoding. Can be used to provide much more"
                " complete address information. Will increase run time significantly for each location that is reverse"
                " geocoded."
            ),
        )

        return options.Options(
            amenity,
            physical_address,
            radius_km,
            deny_list,
            travel_mode,
            max_results,
            attempt_reverse_geocoding,
        )

    @classmethod
    def run(cls) -> options.Options:
        with st.sidebar:
            with st.form("options_form"):
                options = cls.get_options_from_ui()
                st.form_submit_button(
                    "Submit Search",
                    type="primary",
                    use_container_width=True,
                )
        return options


class ValidationSection:
    @staticmethod
    def run(home: geo.Place, places_df: pd.DataFrame) -> bool:
        if home.point is None:
            msg = (
                f'Unable to find latitude and longitude coordinates for physical address "{home.flat_address}", please'
                " try a different search."
            )
            st.error(msg)
            return True

        if places_df.empty:
            msg = "No matches found!"
            st.error(msg)
            return True

        return False


class MapSection:
    @staticmethod
    def run(home: geo.Place, places_df: pd.DataFrame, options: options.Options) -> None:
        folium_map = mapping.generate_map(
            home,
            places_df,
            options.amenity,
            options.radius,
            options.travel_mode,
        )
        st_folium(folium_map, use_container_width=True, returned_objects=[])


class MetricsSection:
    @staticmethod
    def run(df: pd.DataFrame) -> None:
        cols = st.columns(3)
        cols[0].metric("Number of Matches", len(df))
        cols[1].metric("Distance to Nearest Match", f'{df["distance (km)"].min()} km')
        cols[2].metric("Median Distance to All Matches", f'{df["distance (km)"].median()} km')


class TableSection:
    @staticmethod
    def run(df: pd.DataFrame) -> None:
        column_config = {
            "name": st.column_config.TextColumn(
                "Name",
            ),
            "address": st.column_config.TextColumn(
                "Address",
            ),
            "website": st.column_config.LinkColumn(
                "Website",
            ),
            "latitude": st.column_config.NumberColumn(
                "Latitude",
            ),
            "longitude": st.column_config.NumberColumn(
                "Longitude",
            ),
            "distance (km)": st.column_config.NumberColumn(
                "Distance (km)",
            ),
        }

        st.dataframe(df, column_config=column_config, use_container_width=True)

        st.download_button(
            label="Download CSV",
            data=utils.convert_df_to_csv(df),
            file_name="results.csv",
        )
