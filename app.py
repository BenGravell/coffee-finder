import pandas as pd

from app_manager import AppManager
import ui
import utils


def main() -> None:
    with AppManager():
        ui.TitleSection.run()
        options = ui.OptionsSection.run()
        location, places_df = utils.compute_location_and_places_df(options)
        invalid_results = ui.ValidationSection.run(location, places_df)
        if invalid_results:
            return
        assert isinstance(places_df, pd.DataFrame)
        ui.MapSection.run(location, places_df, options)
        ui.MetricsSection.run(places_df)
        ui.TableSection.run(places_df)


if __name__ == "__main__":
    main()
