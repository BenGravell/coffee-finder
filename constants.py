APP_TITLE = "Coffee Finder"
APP_ICON = ":coffee:"

GOOGLE_MAPS_URL_BASE = "https://www.google.com/maps"

NOMINATIM_USER_AGENT = "coffee_finder_app"

TTL = 1 * 60 * 60  # default time-to-live of 1 hour

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

FOLIUM_MAP_DEFAULT_ZOOM_LEVEL = 3
