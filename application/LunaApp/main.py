from kivy.core.window import Window

import registers

Window.maximize()

import webbrowser

from kivy.app import App
from carbonkivy.uix.screenmanager import CScreenManager
from kivy.clock import Clock, mainthread
from kivy.uix.screenmanager import FadeTransition as FT

from View.base_screen import LoadingLayout


Clock.max_iteration = 60


def set_softinput(*args) -> None:
    Window.keyboard_anim_args = {"d": 0.2, "t": "in_out_expo"}
    Window.softinput_mode = "below_target"


Window.on_restore(Clock.schedule_once(set_softinput, 0.1))


class UI(CScreenManager):
    def __init__(self, *args, **kwargs):
        super(UI, self).__init__(*args, **kwargs)
        self.transition = FT(duration=0.05, clearcolor=[1, 1, 1, 0])


class LunaApp(CarbonApp):

    def __init__(self, *args, **kwargs):
        super(LunaApp, self).__init__(*args, **kwargs)
        self.theme = "Gray100"
        self.title = "Luna V1.0"

        self.loading_layout = LoadingLayout()

    def build(self) -> UI:
        self.manager_screens = UI()
        self.generate_application_screens()
        return self.manager_screens

    def generate_application_screens(self) -> None:
        # adds different screen widgets to the screen manager
        import View.screens

        screens = View.screens.screens

        for i, name_screen in enumerate(screens.keys()):
            model = screens[name_screen]["model"]()
            view = screens[name_screen]["object"]()
            view.manager_screens = self.manager_screens
            view.name = name_screen
            view.view_model = model

            self.manager_screens.add_widget(view)

    def referrer(self, destination: str = None) -> None:
        if self.manager_screens.current != destination:
            self.manager_screens.current = destination

    def web_open(self, url: str) -> None:
        webbrowser.open_new_tab(url)

    @mainthread
    def loading_state(
        self, state: bool = False, master: object = Window, *args
    ) -> None:
        try:
            if state:
                master.add_widget(self.loading_layout)
            else:
                master.remove_widget(self.loading_layout)
        except:
            return None


if __name__ == "__main__":
    LunaApp().run()
