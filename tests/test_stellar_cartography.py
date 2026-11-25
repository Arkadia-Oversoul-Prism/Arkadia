"""Tests for the Stellar Cartography engine — the Encyclopedia Galactica readout.

Covers the full celestial readout: Ark Date, Schumann resonance, lunar phase,
planetary sky (bone report), cosmic weather, Oversoul blind-pull, and the
Galactica volume index. Pure-python, deterministic by Ark Day.
"""
import sys
import importlib


def test_stellar_cartography_returns_all_sections():
    from kernel.stellar import stellar_cartography
    d = stellar_cartography()
    for key in ("ark_date", "schumann", "lunar", "planetary",
                "cosmic_weather", "oversoul_blind_pull", "galactica"):
        assert key in d, f"missing section: {key}"


def test_ark_date_in_stellar_matches_canonical_shape():
    from kernel.stellar import stellar_cartography
    ark = stellar_cartography()["ark_date"]
    assert ark["ark_year"] >= 1
    assert ark["ark_total_years"] == 8
    assert ark["total_ark_day"] >= 1
    assert "Y" in ark["display"]
    assert "Birthday Seal" in ark["epoch"]


def test_schumann_has_seven_bands_and_dominant():
    from kernel.stellar import stellar_cartography
    s = stellar_cartography()["schumann"]
    assert len(s["bands"]) == 7
    assert s["dominant_hz"] == s["bands"][s["dominant_index"]]["hz"]
    # 7.83 Hz is the fundamental
    assert s["bands"][0]["hz"] == 7.83
    assert s["quality"]


def test_lunar_phase_illumination_in_range():
    from kernel.stellar import stellar_cartography
    lunar = stellar_cartography()["lunar"]
    assert 0 <= lunar["illumination_pct"] <= 100
    assert lunar["phase"] in {
        "New Moon", "Waxing Crescent", "First Quarter", "Waxing Gibbous",
        "Full Moon", "Waning Gibbous", "Last Quarter", "Waning Crescent",
    }
    assert lunar["glyph"]
    assert lunar["moon_name"]  # has a folk name


def test_planetary_sky_has_bone_report_and_all_bodies():
    from kernel.stellar import stellar_cartography
    p = stellar_cartography()["planetary"]
    for body in ("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"):
        assert body in p["bodies"]
        assert p["bodies"][body]["sign"]
        assert p["bodies"][body]["glyph"]
    assert p["sun_sign"]
    assert p["moon_sign"]
    assert "bone_report" in p
    assert len(p["zodiac"]) == 12


def test_cosmic_weather_pressure_is_classified():
    from kernel.stellar import stellar_cartography
    w = stellar_cartography()["cosmic_weather"]
    assert w["geomagnetic_pressure"] in ("Calm", "Active", "Storm", "Severe")
    assert w["mood"]
    assert w["solar_wind_kms"] > 0
    assert 0 <= w["kp_index"] <= 9


def test_oversoul_blind_pull_returns_transmission():
    from kernel.stellar import stellar_cartography, _OVERSOUL_TRANSMISSIONS
    o = stellar_cartography()["oversoul_blind_pull"]
    assert o["transmission"]
    assert o["transmission"] in _OVERSOUL_TRANSMISSIONS
    assert "blind-pull" in o["method"]


def test_oversoul_transmissions_deterministic_per_ark_day():
    from kernel.stellar import _oversoul_blind_pull
    a = _oversoul_blind_pull(140)
    b = _oversoul_blind_pull(140)
    assert a["transmission"] == b["transmission"]  # same day → same pull


def test_galactica_has_five_volumes():
    from kernel.stellar import stellar_cartography
    g = stellar_cartography()["galactica"]
    assert g["total_volumes"] == 5
    assert len(g["volumes"]) == 5
    assert g["current_volume"] in {v["volume"] for v in g["volumes"]}


def _heavy_module_imports(source: str) -> set[str]:
    """Top-level modules a source file imports from the API/HTTP stack."""
    import ast
    found: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            found.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            found.add(node.module.split(".")[0])
    return found & {"api", "httpx", "fastapi", "starlette"}


def test_stellar_decoupled_from_api_main():
    """kernel/stellar.py must load standalone: no API or HTTP-stack imports."""
    from pathlib import Path
    source = (Path(__file__).resolve().parents[1] / "kernel" / "stellar.py").read_text(
        encoding="utf-8"
    )
    assert _heavy_module_imports(source) == set()
    # Negative control: the detector must flag the coupling it exists to catch.
    assert _heavy_module_imports("from api.main import app\nimport httpx\n") == {"api", "httpx"}
