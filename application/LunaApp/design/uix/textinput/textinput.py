from __future__ import annotations

__all__ = (
    "LTextInput",
    "LTextInputLabel",
    "LTextInputLayout",
    "LTextInputHelperText",
    "LTextInputTrailingIconButton",
)

from kivy.clock import mainthread
from kivy.logger import Logger
from kivy.properties import ObjectProperty
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.textinput import TextInput

from design.behaviors import (
    AdaptiveBehavior,
    BackgroundColorBehaviorCircular,
    DeclarativeBehavior,
    HierarchicalLayerBehavior,
    HoverBehavior,
    StateFocusBehavior,
)
from design.uix.button import LButtonGhost
from design.uix.label import LLabel


class LTextInputHelperText(LLabel):
    pass


class LTextInputLabel(LLabel):
    pass


class LTextInputLayout(
    AdaptiveBehavior,
    BackgroundColorBehaviorCircular,
    StateFocusBehavior,
    RelativeLayout,
    DeclarativeBehavior,
    HierarchicalLayerBehavior,
    HoverBehavior,
):

    ltextinput_area = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs) -> None:
        super(LTextInputLayout, self).__init__(**kwargs)

    def on_kv_post(self, *args):
        self.update_specs()
        return super().on_kv_post(*args)

    @mainthread
    def update_specs(self, *args) -> None:
        if self.ltextinput_area != None:
            self.height = self.ltextinput_area.height
        else:
            Logger.error("LTextInputLayout must contain a single LTextInput widget.")


class LTextInputTrailingIconButton(LButtonGhost):
    pass


class LTextInput(
    AdaptiveBehavior,
    TextInput,
    DeclarativeBehavior,
):

    def __init__(self, **kwargs) -> None:
        super(LTextInput, self).__init__(**kwargs)

    def on_parent(self, *args) -> None:
        if isinstance(self.parent, LTextInputLayout):
            self.parent.ltextinput_area = self
            self.bind(height=self.parent.update_specs)
        else:
            Logger.error("LTextInput must be contained inside LTextInputLayout.")

    def on_password(self, *args) -> None:
        self.cursor = (0, 0)
