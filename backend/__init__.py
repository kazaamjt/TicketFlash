"""
Kultur Klash, copyright 2026
"""

from . import config

__version__ = "0.0.1"
ENVIRONMENT = config.get_multichoice("main", "env", ["dev", "production"], "production")
