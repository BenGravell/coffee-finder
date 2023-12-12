from urllib.parse import urlencode

import constants


def get_directions_link(destination: str, travelmode: str) -> str:
    """Create a Google Maps directions link.

    See https://developers.google.com/maps/documentation/urls/get-started#directions-action for more details.
    """
    params = {
        "destination": destination,
        "travelmode": travelmode,
    }
    return f"{constants.GOOGLE_MAPS_URL_BASE}/dir/?api=1&{urlencode(params)}"
