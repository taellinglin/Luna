from __future__ import annotations

__all__ = ("LScreenManager",)

from kivy.uix.screenmanager import ScreenManager, FadeTransition

from design.behaviors import BackgroundColorBehaviorRectangular, DeclarativeBehavior


class LScreenManager(
    BackgroundColorBehaviorRectangular, ScreenManager, DeclarativeBehavior
):

    def __init__(self, **kwargs):
        super(LScreenManager, self).__init__(**kwargs)
        self.transition = FadeTransition(duration=0.05, clearcolor=[0, 0, 0, 1])
