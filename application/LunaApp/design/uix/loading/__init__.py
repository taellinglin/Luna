import os

from kivy.lang import Builder

from design.config import UIX

from .loading import LLoadingIndicator, LLoadingLayout

filename = os.path.join(UIX, "loading", "loading.kv")
if not filename in Builder.files:
    Builder.load_file(filename)
