"""Constants."""

APP_TITLE = "Coffee Finder"
APP_ICON = ":coffee:"

GOOGLE_MAPS_URL_BASE = "https://www.google.com/maps"

# Need to provide a user agent to nominatim per user agreement
NOMINATIM_USER_AGENT = "coffee_finder_app"

# Need to cast a wide net in the initial query since many results will be invalid
OSM_MAX_RESULTS_MULTIPLIER = 10

# Default time-to-live of 1 hour
TTL = 1 * 60 * 60

AMENITY_OPTIONS = [
    "bar",
    "biergarten",
    "cafe",
    "fast_food",
    "food_court",
    "ice_cream",
    "pub",
    "restaurant",
]

AMENITY_ICON_DICT = {
    "bar": "beer",
    "biergarten": "beer",
    "cafe": "coffee",
    "fast_food": "cutlery",
    "food_court": "cutlery",
    "ice_cream": "diamond",
    "pub": "beer",
    "restaurant": "cutlery",
}

EXCLUDE_TAG_OPTIONS = ["Starbucks", "Dunkin", "Tim Hortons"]
TRAVEL_MODE_OPTIONS = ["walking", "driving"]

FOLIUM_MAP_DEFAULT_ZOOM_LEVEL = 3
