from __future__ import annotations

__all__ = ("LBoxLayout",)

from kivy.uix.boxlayout import BoxLayout

from design.behaviors import (
    AdaptiveBehavior,
    BackgroundColorBehaviorCircular,
    DeclarativeBehavior,
)


class LBoxLayout(
    AdaptiveBehavior,
    BackgroundColorBehaviorCircular,
    BoxLayout,
    DeclarativeBehavior,
):
    pass
