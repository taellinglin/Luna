from __future__ import annotations

__all__ = (
    "LLoadingLayout",
    "LLoadingIndicator",
)

from kivy.clock import Clock
from kivy.properties import (
    BooleanProperty,
    BoundedNumericProperty,
    ColorProperty,
    NumericProperty,
    OptionProperty,
)
from kivy.uix.widget import Widget

from design.behaviors import DeclarativeBehavior, HierarchicalLayerBehavior
from design.uix.anchorlayout import LAnchorLayout


class LLoadingLayout(LAnchorLayout, HierarchicalLayerBehavior):
    pass


class LLoadingIndicator(Widget, HierarchicalLayerBehavior, DeclarativeBehavior):

    active = BooleanProperty(True)

    bg_color = ColorProperty([1, 1, 1, 0])

    stroke_color = ColorProperty()

    angle = NumericProperty(0)

    stroke_width = NumericProperty(5)

    angular_velocity = BoundedNumericProperty(8, min=2)

    rotation_interval = BoundedNumericProperty(60, min=10)

    role = OptionProperty("Small", options=["Large", "Small"])

    def __init__(self, **kwargs) -> None:
        super(LLoadingIndicator, self).__init__(**kwargs)
        self.on_active()

    def rotate(self, *args) -> None:
        self.angle = (self.angle + self.angular_velocity) % 360

    def on_active(self, *args) -> None:
        if self.active:
            Clock.schedule_interval(self.rotate, 1 / self.rotation_interval)
        elif not self.active:
            Clock.unschedule(self.update)
