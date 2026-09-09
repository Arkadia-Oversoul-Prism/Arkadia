"""Arkadia Engineering Lab v0.1: deterministic, read-only intelligence."""
SCHEMA_VERSION = "0.1"
COLLECTOR_VERSION = "lab-0.1"
ANALYSIS_VERSION = "lab-0.1"

from .service import build_overview

__all__ = ["build_overview", "SCHEMA_VERSION", "COLLECTOR_VERSION", "ANALYSIS_VERSION"]
