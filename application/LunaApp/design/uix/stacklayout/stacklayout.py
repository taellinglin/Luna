from __future__ import annotations

__all__ = ("LStackLayout",)

from kivy.uix.stacklayout import StackLayout

from design.behaviors import (
    AdaptiveBehavior,
    BackgroundColorBehaviorRectangular,
    DeclarativeBehavior,
)


class LStackLayout(
    AdaptiveBehavior,
    BackgroundColorBehaviorRectangular,
    StackLayout,
    DeclarativeBehavior,
):
    pass
