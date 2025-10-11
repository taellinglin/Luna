import os

from kivy.lang import Builder

from design.config import UIX

from .label import LLabel

filename = os.path.join(UIX, "label", "label.kv")
if not filename in Builder.files:
    Builder.load_file(filename)
