from typing import Literal
from types import TracebackType

import streamlit as st  # type: ignore[import-not-found]
from streamlit_extras.metric_cards import style_metric_cards  # type: ignore[import-not-found]

import constants
import geo
import streamlit_config


def set_up_streamlit() -> None:
    st.set_page_config(
        page_title=constants.APP_TITLE,
        page_icon=constants.APP_ICON,
        layout="wide",
    )

    style_metric_cards(
        border_left_color=streamlit_config.STREAMLIT_CONFIG["theme"]["primaryColor"],
        border_color=streamlit_config.STREAMLIT_CONFIG["theme"]["secondaryBackgroundColor"],
        background_color=streamlit_config.STREAMLIT_CONFIG["theme"]["backgroundColor"],
        border_size_px=2,
        border_radius_px=20,
        box_shadow=False,
    )


def initialize_session_state() -> None:
    st.session_state.overpass_api = geo.create_overpass_api()
    st.session_state.geolocator = geo.create_geocoder()
    st.session_state.initialized = True


class AppManager:
    def __enter__(self) -> "AppManager":
        set_up_streamlit()
        if not st.session_state.get("initialized"):
            initialize_session_state()
        return self

    def __exit__(
        self, exc_type: BaseException | None, exc_value: BaseException | None, traceback: TracebackType | None
    ) -> Literal[False]:
        return False
