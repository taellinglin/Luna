from __future__ import annotations

__all__ = ("LScrollView",)

from kivy.effects.opacityscroll import OpacityScrollEffect
from kivy.metrics import dp
from kivy.uix.scrollview import ScrollView

from design.behaviors import BackgroundColorBehaviorRectangular, DeclarativeBehavior


class LScrollView(BackgroundColorBehaviorRectangular, ScrollView, DeclarativeBehavior):

    effect_cls = OpacityScrollEffect
