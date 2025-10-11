from __future__ import annotations

__all__ = ("LRelativeLayout",)

from kivy.uix.relativelayout import RelativeLayout

from design.behaviors import (
    AdaptiveBehavior,
    BackgroundColorBehaviorRectangular,
    DeclarativeBehavior,
)


class LRelativeLayout(
    AdaptiveBehavior,
    BackgroundColorBehaviorRectangular,
    RelativeLayout,
    DeclarativeBehavior,
):
    pass
