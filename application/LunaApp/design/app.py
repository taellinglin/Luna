from __future__ import annotations

__all__ = ("LunaApp",)

import os

from kivy.app import App
from kivy.lang import Builder
from kivy.logger import Logger

from design.theme.theme import LunaTheme
from design.utils import update_system_ui


class LunaApp(App, LunaTheme):
    """
    The Main App class inherits from LunaTheme to update the theme and appropriate colors based on the given theme.
    """

    def __init__(self, **kwargs) -> None:
        super(LunaApp, self).__init__(**kwargs)
        update_system_ui(self.background, self.background, "Dark")

    def load_all_kv_files(self, directory: str, *args) -> None:
        """
        Recursively load all kv files from a given directory.
        """

        for root, dirs, files in os.walk(directory):
            for file in files:
                if (
                    os.path.splitext(file)[1] == ".kv"
                    and file != "style.kv"  # if use PyInstaller
                    and "__MACOS" not in root  # if use Mac OS
                ):
                    path_to_kv_file = os.path.join(root, file)
                    if not path_to_kv_file in Builder.files:
                        Builder.load_file(path_to_kv_file)
