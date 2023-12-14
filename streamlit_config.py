"""Load and expose the .streamlit/config.toml file as a Python dict."""

from pathlib import Path

import tomllib

with Path("./.streamlit/config.toml").open("rb") as f:
    STREAMLIT_CONFIG = tomllib.load(f)
