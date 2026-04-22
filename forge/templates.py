"""
Arkadia Forge — Archetype Registry.

The registry is generic from day one. Each archetype is a callable that takes a
short scene prompt from the sovereign and wraps it in a high-fidelity keyword
stack. Today: Auralis. Tomorrow: Eden Sanctuary, Scroll Art, Vhix, etc.

Add a new archetype with:
    @registry.register("name")
    def my_preset(scene: str) -> str: ...
"""
from typing import Callable, Dict, List


# ─── Keyword fragments — Auralis "Blood and Bones" ────────────────────────────

AURALIS_FLAME_VESSEL = (
    "ancient-futuristic high priestess, ethereal matriarch, "
    "luminescent obsidian and solar-gold skin, piercing illuminated eyes, "
    "intricate geometric golden headdress as energetic receiver"
)

AURALIS_ACTIVE_GRID = (
    "megalithic ruins as active energy grid, glowing golden sacred geometry "
    "overlaid on ancient stone, luminous ley lines, deep indigo and solar gold palette"
)

AURALIS_COMPOSITING = (
    "pure deep cosmic background, high contrast subject-field separation, "
    "centered composition with negative space for double-exposure compositing"
)

AURALIS_RENDER = (
    "hyper-realistic cinematic portrait, 8k resolution, Unreal Engine 5 render, "
    "cinematic bloom, volumetric light, deep cosmic lighting"
)

AURALIS_NEGATIVE = (
    "no jewelry framing, no fashion shoot, no contemporary backdrop, "
    "no flat lighting, no decorative ornament without geometric purpose, "
    "no dead ruin aesthetic"
)


# ─── Registry ─────────────────────────────────────────────────────────────────

class ForgeRegistry:
    """Maps archetype name → preset function (scene -> compiled prompt)."""

    def __init__(self) -> None:
        self._presets: Dict[str, Callable[[str], str]] = {}

    def register(self, name: str) -> Callable[[Callable[[str], str]], Callable[[str], str]]:
        def decorator(fn: Callable[[str], str]) -> Callable[[str], str]:
            self._presets[name.lower()] = fn
            return fn
        return decorator

    def compile(self, archetype: str, scene: str) -> str:
        key = (archetype or "").strip().lower()
        if key not in self._presets:
            raise KeyError(f"Unknown archetype '{archetype}'. Known: {self.list()}")
        return self._presets[key](scene.strip())

    def list(self) -> List[str]:
        return sorted(self._presets.keys())


registry = ForgeRegistry()


# ─── Presets ──────────────────────────────────────────────────────────────────

@registry.register("auralis")
def auralis_preset(scene: str) -> str:
    """
    Compile a sovereign scene fragment into the full Auralis aesthetic.
    Example input: "meditating under the Sahara-Agartha bridge"
    """
    scene_clause = f"Scene: {scene}." if scene else ""
    return (
        f"{scene_clause} "
        f"Subject: {AURALIS_FLAME_VESSEL}. "
        f"Environment: {AURALIS_ACTIVE_GRID}. "
        f"Composition: {AURALIS_COMPOSITING}. "
        f"Render: {AURALIS_RENDER}. "
        f"Avoid: {AURALIS_NEGATIVE}."
    ).strip()
