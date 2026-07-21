"""
Kultur Klash, copyright 2026
"""

from . import config

__version__ = "0.0.1"
PRODUCTION = config.get_bool("env", "prod", False)
