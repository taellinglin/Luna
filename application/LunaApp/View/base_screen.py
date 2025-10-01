from typing import Literal

from Utility.observer import Observer

from kivy.properties import ObjectProperty
from kivy.app import App
from kivy.input.providers.mouse import MouseMotionEvent
from carbonkivy.uix.screen import CScreen
from carbonkivy.uix.loading import CLoadingLayout


class LoadingLayout(CLoadingLayout):

    def __init__(self, **kwargs) -> None:
        super(LoadingLayout, self).__init__(**kwargs)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            return (
                True  # Prevent touch events from propagating to the underlying widgets
            )
        return super(LoadingLayout, self).on_touch_down(touch)

    def on_touch_move(self, touch: MouseMotionEvent) -> Literal[True] | None:
        if self.collide_point(*touch.pos):
            return (
                True  # Prevent touch events from propagating to the underlying widgets
            )
        return super(LoadingLayout, self).on_touch_move(touch)

    def on_touch_up(self, touch: MouseMotionEvent) -> Literal[True] | None:
        if self.collide_point(*touch.pos):
            return (
                True  # Prevent touch events from propagating to the underlying widgets
            )
        return super(LoadingLayout, self).on_touch_up(touch)


class BaseScreenView(CScreen, Observer):

    manager_screens = ObjectProperty()
    """
    Screen manager object - :class:`~carbonkivy.uix.screenmanager.MDScreenManager`.

    :attr:`manager_screens` is an :class:`~kivy.properties.ObjectProperty`
    and defaults to `None`.
    """

    view_model = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs) -> None:
        super(BaseScreenView, self).__init__(**kwargs)
        # Often you need to get access to the application object from the view
        # class. You can do this using this attribute.
        self.app = App.get_running_app()

    def on_view_model(self, instance: object, value: object) -> None:
        """
        This method is called when the view model is set.
        It adds the view as an observer to the model.
        """
        if value is not None:
            value.add_observer(self)
