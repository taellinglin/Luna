from __future__ import annotations

__all__ = ("LFloatLayout",)

from kivy.uix.floatlayout import FloatLayout

from design.behaviors import (
    AdaptiveBehavior,
    BackgroundColorBehaviorRectangular,
    DeclarativeBehavior,
)


class LFloatLayout(
    AdaptiveBehavior,
    BackgroundColorBehaviorRectangular,
    FloatLayout,
    DeclarativeBehavior,
):
    pass
