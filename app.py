from app_manager import AppManager
import geo
import ui
import utils


def main() -> None:
    with AppManager():
        ui.TitleSection.run()
        options = ui.OptionsSection.run()
        home = geo.Place(address=options.physical_address)
        places_df = utils.compute_places_df(options, home)
        invalid_results = ui.ValidationSection.run(home, places_df)
        if invalid_results:
            return
        ui.MapSection.run(home, places_df, options)
        ui.MetricsSection.run(places_df)
        ui.TableSection.run(places_df)


if __name__ == "__main__":
    main()
