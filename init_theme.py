#!/usr/bin/env python3
"""Extract dominant colors from wallpaper and write theme.css."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config.json"
THEME_PATH = ROOT / "theme.css"


def load_config() -> dict:
    with CONFIG_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02x}{g:02x}{b:02x}"


def saturation(r: int, g: int, b: int) -> float:
    r_f, g_f, b_f = r / 255.0, g / 255.0, b / 255.0
    mx = max(r_f, g_f, b_f)
    mn = min(r_f, g_f, b_f)
    if mx == 0:
        return 0.0
    return (mx - mn) / mx


def luminance(r: int, g: int, b: int) -> float:
    return 0.299 * r + 0.587 * g + 0.114 * b


def assign_colors(palette: list[tuple[int, int, int]]) -> dict[str, str]:
    if not palette:
        raise ValueError("Empty palette")

    unique = list(dict.fromkeys(palette))
    if len(unique) < 4:
        while len(unique) < 4:
            unique.append(unique[-1])

    by_luminance = sorted(unique, key=lambda c: luminance(*c))
    by_saturation = sorted(unique, key=lambda c: saturation(*c), reverse=True)

    base = by_luminance[0]
    text = by_luminance[-1]
    accent = by_saturation[0]
    secondary = by_saturation[1] if len(by_saturation) > 1 else by_saturation[0]

    if saturation(*accent) < 0.12 or luminance(*text) - luminance(*base) < 20:
        raise ValueError("Palette lacks sufficient contrast or saturation")

    accent_hex = rgb_to_hex(*accent)
    return {
        "base": rgb_to_hex(*base),
        "accent": accent_hex,
        "secondary": rgb_to_hex(*secondary),
        "text": rgb_to_hex(*text),
        "text_dim": f"color-mix(in srgb, {accent_hex} 50%, transparent)",
    }


def extract_palette(wallpaper_path: Path) -> list[tuple[int, int, int]]:
    from colorthief import ColorThief

    thief = ColorThief(str(wallpaper_path))
    return thief.get_palette(color_count=5, quality=1)


def fallback_colors(theme_cfg: dict) -> dict[str, str]:
    accent = theme_cfg.get("fallback_accent", "#7dcfff")
    return {
        "base": theme_cfg.get("fallback_base", "#1a1b26"),
        "accent": accent,
        "secondary": theme_cfg.get("fallback_secondary", "#bb9af7"),
        "text": "#c0caf5",
        "text_dim": f"color-mix(in srgb, {accent} 50%, transparent)",
    }


def write_theme_css(colors: dict[str, str]) -> None:
    css = f""":root {{
  --color-base: {colors["base"]};
  --color-accent: {colors["accent"]};
  --color-secondary: {colors["secondary"]};
  --color-text: {colors["text"]};
  --color-text-dim: {colors["text_dim"]};
}}
"""
    THEME_PATH.write_text(css, encoding="utf-8")


def generate_theme() -> dict[str, str]:
    config = load_config()
    theme_cfg = config.get("theme", {})
    wallpaper_rel = config.get("wallpaper", "static/wallpapers/current.jpg")
    wallpaper_path = ROOT / wallpaper_rel

    try:
        if not wallpaper_path.is_file():
            raise FileNotFoundError(f"Wallpaper not found: {wallpaper_path}")
        palette = extract_palette(wallpaper_path)
        colors = assign_colors(palette)
    except Exception as exc:
        print(f"[init_theme] Using fallback colors: {exc}", file=sys.stderr)
        colors = fallback_colors(theme_cfg)

    write_theme_css(colors)
    print(f"[init_theme] Wrote {THEME_PATH}")
    return colors


if __name__ == "__main__":
    generate_theme()
