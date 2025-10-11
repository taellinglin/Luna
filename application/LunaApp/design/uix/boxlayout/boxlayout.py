from __future__ import annotations

__all__ = ("LBoxLayout",)

from kivy.uix.boxlayout import BoxLayout

from design.behaviors import (
    AdaptiveBehavior,
    BackgroundColorBehaviorRectangular,
    DeclarativeBehavior,
)


class LBoxLayout(
    AdaptiveBehavior,
    BackgroundColorBehaviorRectangular,
    BoxLayout,
    DeclarativeBehavior,
):
    pass
