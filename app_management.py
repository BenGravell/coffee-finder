"""Management of the streamlit app."""
from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import streamlit as st  # type: ignore[import-not-found]
from streamlit_extras.metric_cards import style_metric_cards  # type: ignore[import-not-found]

import constants
import geo
import streamlit_config

if TYPE_CHECKING:
    from types import TracebackType

    from typing_extensions import Self


def set_up_streamlit() -> None:
    """Set up the Streamlit application environment and styling.

    This function configures various settings and styling for a Streamlit application,
    such as page title, page icon, and custom card styling. It ensures that the Streamlit
    application is visually consistent and visually appealing.
    """
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
    """Initialize the session state for the Streamlit application.

    This function sets up and initializes the session state for the Streamlit application.
    It creates and stores necessary objects and variables in the session state, such as
    Overpass API and geolocation services, to be used throughout the application's session.
    """
    st.session_state.overpass_api = geo.create_overpass_api()
    st.session_state.geolocator = geo.create_geocoder()
    st.session_state.initialized = True


class AppManager:
    """Context manager for managing the Streamlit application setup and session state."""

    def __enter__(self) -> Self:
        """Enter the context and set up the Streamlit application environment.

        This method is automatically called when entering the context created by the
        `with` statement. It initializes the Streamlit application and session state.
        """
        set_up_streamlit()
        if not st.session_state.get("initialized"):
            initialize_session_state()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> Literal[False]:
        """Exit the context.

        This method is automatically called when exiting the context created by the `with`
        statement. It simply returns `False`, indicating that any exceptions raised within
        the context should not be suppressed.
        """
        return False
