from __future__ import annotations

__all__ = ("LScreen",)

from kivy.uix.screenmanager import Screen

from design.behaviors import BackgroundColorBehaviorRectangular, DeclarativeBehavior


class LScreen(BackgroundColorBehaviorRectangular, Screen, DeclarativeBehavior):
    pass
