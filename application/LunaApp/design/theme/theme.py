from __future__ import annotations

__all__ = ("LunaTheme",)

import os

from kivy.core.window import Window
from kivy.event import EventDispatcher
from kivy.lang import Builder
from kivy.properties import ListProperty, OptionProperty
from kivy.utils import colormap, get_color_from_hex

from design.config import THEME
from design.theme.color_tokens import static_tokens, thematic_tokens
from design.theme.colors import StaticColors, ThematicColors

filename = os.path.join(THEME, "theme.kv")
if not filename in Builder.files:
    Builder.load_file(filename)


class LunaTheme(EventDispatcher, ThematicColors, StaticColors):

    theme = OptionProperty("light", options=["light", "dark"])

    thematic_color_tokens = ListProperty(list(thematic_tokens.keys()))

    static_color_tokens = ListProperty(list(static_tokens.keys()))

    color_tokens = ListProperty(
        list(thematic_tokens.keys()) + list(static_tokens.keys())
    )

    def __init__(self, **kwargs) -> None:
        super(LunaTheme, self).__init__(**kwargs)
        self.on_theme()

    def on_theme(self, *args) -> None:
        colormap.update(self.parse_thematic_tokens())
        Window.clearcolor = colormap["background"]
        self.update_thematic_colors()

    def parse_thematic_tokens(self, *args) -> dict:
        tokenmap = {}
        for token, values in thematic_tokens.items():
            color_value = values[self.theme]
            if isinstance(color_value, tuple):  # Handle (hex, alpha)
                rgba = get_color_from_hex(color_value[0])
                rgba[3] = color_value[1]  # Set transparency
            else:
                rgba = get_color_from_hex(color_value)
            tokenmap[token] = rgba
        return tokenmap

    def update_thematic_colors(self, *args) -> None:
        for token in self.thematic_color_tokens:
            setattr(self, token, colormap[token])
