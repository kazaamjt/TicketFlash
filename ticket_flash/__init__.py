"""
Kultur Klash, copyright 2026
"""

from . import config

__version__ = "0.0.1"
DEVMODE = config.get_bool("dev", "mode", False)
PRODUCTION = config.get_bool("env", "prod", False)
