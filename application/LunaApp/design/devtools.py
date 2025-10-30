import glob
import os

from kaki.app import App
from kivy.lang import Builder


class LiveApp(App):

    def __init__(self, **kwargs) -> None:
        super(LiveApp, self).__init__(**kwargs)
        self.DEBUG = True
        self.CLASSES = {self.root: "main"}  # main file name or root file name

        self.AUTORELOADER_PATHS = [
            (self.kv_directory, {"recursive": True}),
        ]
        for file in glob.glob(
            os.path.join(self.kv_directory, "**", "*.kv"), recursive=True
        ):
            self.KV_FILES.append(file)