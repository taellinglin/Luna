from __future__ import annotations

__all__ = ("LBaseIcon", "LIcon", "LIconCircular")

import os

from kivy.properties import ColorProperty, OptionProperty
from kivy.uix.label import Label

from design.behaviors import (
    AdaptiveBehavior,
    BackgroundColorBehaviorCircular,
    BackgroundColorBehaviorRectangular,
    DeclarativeBehavior,
)
from design.config import DATA
from design.theme.icons import ibm_icons


class LBaseIcon(AdaptiveBehavior, DeclarativeBehavior, Label):
    """
    The LBaseIcon class inherits from Label to display icons from IBM's icon library using the generated icon font.
    """

    icon = OptionProperty("", options=ibm_icons.keys())

    _color = ColorProperty(None, allownone=True)

    font_name = os.path.join(DATA, "Icons", "carbondesignicons.ttf")

    def __init__(self, **kwargs) -> None:
        super(LBaseIcon, self).__init__(**kwargs)

    def on_icon(self, *args) -> None:
        self.text = ibm_icons[self.icon]


class LIcon(BackgroundColorBehaviorRectangular, LBaseIcon):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_kv_post(self, base_widget):
        super().on_kv_post(base_widget)
        self.canvas.remove_group("backgroundcolor-behavior-bg-color")
        self.canvas.remove_group("Background_instruction")


class LIconCircular(BackgroundColorBehaviorCircular, LBaseIcon):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_kv_post(self, base_widget):
        super().on_kv_post(base_widget)
        self.canvas.remove_group("backgroundcolor-behavior-bg-color")
        self.canvas.remove_group("Background_instruction")
