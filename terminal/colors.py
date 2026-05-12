from enum import Enum


class ColorScheme(Enum):
    DEFAULT = "default"
    GREEN = "green"
    AMBER = "amber"
    WHITE = "white"


DEFAULT_COMPANY_COLORS = {
    "A": "red",
    "B": "green",
    "C": "yellow",
    "D": "blue",
    "E": "magenta",
}


RETRO_GREEN_COMPANY_COLORS = {
    symbol: "green"
    for symbol in DEFAULT_COMPANY_COLORS
}


RETRO_AMBER_COMPANY_COLORS = {
    symbol: "yellow"
    for symbol in DEFAULT_COMPANY_COLORS
}


RETRO_WHITE_COMPANY_COLORS = {
    symbol: "white"
    for symbol in DEFAULT_COMPANY_COLORS
}


COMPANY_COLOR_PALETTES = {
    ColorScheme.DEFAULT: DEFAULT_COMPANY_COLORS,
    ColorScheme.GREEN: RETRO_GREEN_COMPANY_COLORS,
    ColorScheme.AMBER: RETRO_AMBER_COMPANY_COLORS,
    ColorScheme.WHITE: RETRO_WHITE_COMPANY_COLORS,
}


def get_company_color(symbol, color_scheme=ColorScheme.DEFAULT):
    palette = COMPANY_COLOR_PALETTES.get(color_scheme, DEFAULT_COMPANY_COLORS)
    return palette.get(symbol, "white")