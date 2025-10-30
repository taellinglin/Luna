from __future__ import annotations

__all__ = (
    "LLink",
    "LLinkIcon",
    "LLinkText",
)

import webbrowser

from kivy.clock import Clock
from kivy.logger import Logger
from kivy.properties import (
    BooleanProperty,
    ColorProperty,
    NumericProperty,
    OptionProperty,
    StringProperty,
)
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout

from design.behaviors import (
    AdaptiveBehavior,
    BackgroundColorBehaviorRectangular,
    HoverBehavior,
    StateFocusBehavior,
)
from design.uix.icon import LIcon
from design.uix.label import LLabel


class LLink(
    AdaptiveBehavior,
    BackgroundColorBehaviorRectangular,
    StateFocusBehavior,
    ButtonBehavior,
    HoverBehavior,
    BoxLayout,
):

    cstate = OptionProperty(
        "normal", options=["active", "disabled", "normal", "visited"]
    )

    external = BooleanProperty(False)

    font_size = NumericProperty()

    role = OptionProperty("Medium", options=["Small", "Medium", "Large"])

    text = StringProperty()

    text_color = ColorProperty()

    text_color_focus = ColorProperty()

    text_color_disabled = ColorProperty()

    text_color_hover = ColorProperty()

    text_color_visited = ColorProperty()

    _text_color = ColorProperty()

    url = StringProperty()

    def __init__(self, **kwargs) -> None:
        super(LLink, self).__init__(**kwargs)

    def on_text_color(self, *args) -> None:
        self._text_color = self.text_color

    def on_focus(self, *args) -> None:
        if self.focus:
            self._text_color = self.text_color_focus
        else:
            self._text_color = self.text_color
        return super().on_focus(*args)

    def on_hover(self, *args) -> None:
        if self.hover:
            self._text_color = self.text_color_hover
        else:
            if not self.focus:
                self._text_color = self.text_color

    def on_touch_down(self, touch) -> bool:
        super().on_touch_down(touch)
        if self.cstate != "disabled":
            if self.focus and self.external:
                Clock.schedule_once(lambda e: webbrowser.open_new_tab(self.url))
        return super().on_touch_down(touch)


class LLinkText(LLabel):

    def __init__(self, **kwargs) -> None:
        super(LLink, self).__init__(**kwargs)

    def on_parent(self, *args) -> None:
        if not isinstance(self.parent, LLink):
            Logger.error("CLinkText must be children widget of LLink only.")


class LLinkIcon(LIcon):

    def __init__(self, **kwargs) -> None:
        super(LLinkIcon, self).__init__(**kwargs)

    def on_parent(self, *args) -> None:
        if not isinstance(self.parent, LLink):
            Logger.error("LLinkLabel must be children widget of LLink only.")
