from __future__ import annotations

__all__ = ("LLabel",)

from kivy.properties import NumericProperty, OptionProperty
from kivy.uix.label import Label

from design.behaviors import (
    AdaptiveBehavior,
    BackgroundColorBehaviorCircular,
    DeclarativeBehavior,
)
from design.theme.size_tokens import font_style_tokens


class LLabel(
    AdaptiveBehavior, BackgroundColorBehaviorCircular, DeclarativeBehavior, Label
):

    style = OptionProperty("body_compact_02", options=font_style_tokens.keys())

    typeface = OptionProperty(
        "IBM Plex Sans", options=["IBM Plex Sans", "IBM Plex Serif", "IBM Plex Mono"]
    )

    weight_style = OptionProperty(
        "Regular",
        options=[
            "Bold",
            "BoldItalic",
            "ExtraLight",
            "ExtraLightItalic",
            "Italic",
            "Light",
            "LightItalic",
            "Medium",
            "MediumItalic",
            "Regular",
            "SemiBold",
            "SemiBoldItalic",
            "Thin",
            "ThinItalic",
        ],
    )

    _font_size = NumericProperty(None, allownone=True)

    def __init__(self, **kwargs) -> None:
        super(LLabel, self).__init__(**kwargs)

    def on_kv_post(self, base_widget):
        self.canvas.remove_group("backgroundcolor-behavior-bg-color")
        self.canvas.remove_group("Background_instruction")
        return super().on_kv_post(base_widget)
