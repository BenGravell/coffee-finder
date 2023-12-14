"""Streamlit app to find coffee."""

import data_processing
import geo
import ui
from app_management import AppManager


def run_app() -> None:
    """Run the entire app."""
    with AppManager():
        ui.TitleSection.run()
        options = ui.OptionsSection.run()
        home = geo.Place(address=options.physical_address)
        places_df = data_processing.compute_places_df(options, home)
        invalid_results = ui.ValidationSection.run(home, places_df)
        if invalid_results:
            return
        ui.MapSection.run(home, places_df, options)
        ui.MetricsSection.run(places_df)
        ui.TableSection.run(places_df)


if __name__ == "__main__":
    run_app()
