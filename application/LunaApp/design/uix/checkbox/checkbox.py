from __future__ import annotations

__all__ = ("LCheckbox",)

from kivy.input.providers.mouse import MouseMotionEvent
from kivy.uix.behaviors import ButtonBehavior
from kivy.properties import BooleanProperty, ColorProperty

from design.behaviors import (
    StateFocusBehavior,
)
from design.uix.icon import LIconCircular


class LCheckbox(
    LIconCircular,
    StateFocusBehavior,
    ButtonBehavior,
):
    """
    LCheckbox is a custom checkbox widget that inherits from AdaptiveBehavior,
    LIconCircular, StateFocusBehavior, ButtonBehavior.
    """

    active = BooleanProperty(False)

    def __init__(self, **kwargs):
        super(LCheckbox, self).__init__(**kwargs)

    def on_touch_down(self, touch: MouseMotionEvent) -> bool:
        if self.collide_point(*touch.pos):
            self.active = not self.active
        return super().on_touch_down(touch)
