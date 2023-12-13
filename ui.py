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
        amenity = st.selectbox(
            label="Amenity",
            options=constants.AMENITY_OPTIONS,
            format_func=lambda x: x.replace("_", " ").title(),
            index=constants.AMENITY_OPTIONS.index("cafe"),
            help="See https://wiki.openstreetmap.org/wiki/Key:amenity for details.",
        )

        street = st.text_input(
            "Street Address (optional)",
            value="1 Summer St",
        )
        city = st.text_input(
            "City",
            value="Boston",
        )
        state = st.text_input(
            "State",
            value="MA",
            help="Can use full state name or two-letter abbreviation.",
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
            value=1.6,
            step=0.1,
            format="%.1f",
        )
        deny_list = st.multiselect(
            "Exclude Tags",
            ["Starbucks", "Dunkin"],
            ["Starbucks", "Dunkin"],
        )
        travel_mode = st.selectbox(
            "Travel Mode for Google Maps directions",
            options=["walking", "driving"],
            format_func=lambda x: x.title(),
        )
        max_results = st.number_input(
            label="Maximum Number of Results",
            min_value=1,
            max_value=1000,
            value=100,
        )
        attempt_reverse_geocoding = st.toggle(
            "Attempt Reverse Geocoding for missing address from OpenStreetMaps?",
            help=(
                "Use latitude and longitude coordinates for reverse geocoding. Can be used to provide much more"
                " complete address information. Will increase run time for each location that is reverse geocoded."
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
        cols = st.columns(2)
        cols[0].metric("Number of Matches", len(df))
        cols[1].metric("Nearest Match", f'{df["distance (km)"].min()} km')


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
