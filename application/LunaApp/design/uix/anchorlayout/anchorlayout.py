from __future__ import annotations

__all__ = ("LAnchorLayout",)

from kivy.uix.anchorlayout import AnchorLayout

from design.behaviors import (
    AdaptiveBehavior,
    BackgroundColorBehaviorRectangular,
    DeclarativeBehavior,
)


class LAnchorLayout(
    AdaptiveBehavior,
    BackgroundColorBehaviorRectangular,
    AnchorLayout,
    DeclarativeBehavior,
):
    pass
