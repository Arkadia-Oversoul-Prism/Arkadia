"""
Arkadia Code Weaver Module

Exports the core components of the weaver package, including the
RecursiveEngine scaffold and a lightweight logger helper.
"""

from .logger import get_logger
from .recursive import RecursiveEngine

__all__ = ["get_logger", "RecursiveEngine"]
