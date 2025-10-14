from __future__ import annotations

__all__ = (
    "LButton",
    "LButtonDanger",
    "LButtonIcon",
    "LButtonLabel",
    "LButtonPrimary",
    "LButtonSecondary",
    "LButtonGhost",
    "LButtonTertiary",
)

from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.properties import (
    BooleanProperty,
    ColorProperty,
    NumericProperty,
    ObjectProperty,
    OptionProperty,
    StringProperty,
    VariableListProperty,
)
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.relativelayout import RelativeLayout

from design.behaviors import (
    AdaptiveBehavior,
    BackgroundColorBehaviorCircular,
    DeclarativeBehavior,
    HoverBehavior,
    StateFocusBehavior,
)
from design.uix.icon import LIcon
from design.uix.label import LLabel


class LButton(
    AdaptiveBehavior,
    BackgroundColorBehaviorCircular,
    StateFocusBehavior,
    ButtonBehavior,
    DeclarativeBehavior,
    HoverBehavior,
    RelativeLayout,
):

    dynamic_width = BooleanProperty(True)

    icon_color = ColorProperty([1, 1, 1, 1])

    text_color = ColorProperty([1, 1, 1, 1])

    text_color_focus = ColorProperty([1, 1, 1, 1])

    text_color_disabled = ColorProperty()

    text_color_hover = ColorProperty()

    _text_color = ColorProperty()

    lbutton_layout = ObjectProperty()

    role = OptionProperty(
        "Medium",
        options=[
            "Small",
            "Medium",
            "Large Productive",
            "Large Expressive",
            "Extra Large",
            "2XL",
        ],
    )

    actual_width = NumericProperty()

    font_size = NumericProperty()

    _width = NumericProperty()

    text = StringProperty(None, allownone=True)

    icon = StringProperty(None, allownone=True)

    padding = VariableListProperty([0], length=4)

    def __init__(self, **kwargs) -> None:
        super(LButton, self).__init__(**kwargs)

    def on_font_size(self, *args) -> None:
        try:
            self.ids.lbutton_layout_icon.font_size = self.font_size + sp(8)
        except Exception:
            return

    def on_text_color(self, instance: object, color: list | str) -> None:
        self._text_color = color
        self.icon_color = color

    def on_icon(self, *args) -> None:

        def add_icon(*args) -> None:
            try:
                self.add_widget(self.lbutton_layout_icon)
                self.ids["lbutton_layout_icon"] = self.lbutton_layout_icon
                return
            except Exception:
                return

        if self.icon and (not "lbutton_layout_icon" in self.ids):
            self.lbutton_layout_icon = LButtonIcon(
                base_button=self,
            )
            Clock.schedule_once(add_icon)
        elif self.icon == None:
            try:
                self.remove_widget(self.ids.lbutton_layout_icon)
            except Exception:
                return
        else:
            try:
                self.ids.lbutton_layout_icon.icon = self.icon
                return
            except Exception:
                return

    def on_text(self, *args) -> None:

        def add_label(*args) -> None:
            try:
                self.add_widget(self.lbutton_layout_label, index=0)
                self.ids["lbutton_layout_label"] = self.lbutton_layout_label
                self.adjust_width()
                return
            except Exception:
                return

        if self.text and (not "lbutton_layout_label" in self.ids):
            self.lbutton_layout_label = LButtonLabel(base_button=self)
            Clock.schedule_once(add_label)
        elif self.text == None:
            try:
                self.remove_widget(self.ids.lbutton_layout_label)
            except Exception:
                return
        else:
            try:
                self.ids.lbutton_layout_label.text = self.text
                self.adjust_width()
                return
            except Exception:
                return

    def on_hover(self, *args) -> None:
        if self.hover:
            self._text_color = self.text_color_hover
        else:
            self._text_color = self.text_color
        self.icon_color = self._text_color
        return super().on_hover(*args)

    def on_state(self, *args) -> None:
        if self.state == "down" and self.cstate != "disabled":
            self._bg_color = self.active_color
        else:
            self._bg_color = (
                (self.bg_color_focus if self.focus else self.bg_color)
                if not self.hover
                else self.hover_color
            )

    def on_focus(self, *args) -> None:
        if self.focus:
            if not self.hover:
                self._bg_color = self.bg_color_focus
            self._text_color = self.text_color_focus
        else:
            self._text_color = self.text_color
        self.icon_color = self._text_color
        return super().on_focus(*args)

    def adjust_width(self, *args) -> None:
        if self.dynamic_width == True:
            _width = dp(0)
            if self.ids.get("lbutton_layout_label"):
                _width += self.ids.lbutton_layout_label.width
                self._width = _width + dp(80)


class LButtonDanger(LButton):

    variant = OptionProperty("Primary", options=["Ghost", "Primary", "Tertiary"])

    def __init__(self, **kwargs) -> None:
        super(LButtonDanger, self).__init__(**kwargs)

    def on_focus(self, *args) -> None:
        if self.variant == "Tertiary":
            self.hover_enabled = not self.focus
        return super().on_focus(*args)


class LButtonIcon(LIcon):

    base_button = ObjectProperty()


class LButtonLabel(LLabel):

    base_button = ObjectProperty()


class LButtonPrimary(LButton):
    pass


class LButtonSecondary(LButton):
    pass


class LButtonGhost(LButton):
    pass


class LButtonTertiary(LButton):

    def __init__(self, **kwargs) -> None:
        super(LButtonTertiary, self).__init__(**kwargs)

    def on_focus(self, *args) -> None:
        self.hover_enabled = not self.focus
        return super().on_focus(*args)
