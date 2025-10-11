import os

from kivy.lang import Builder

from design.config import UIX

from .icon import LBaseIcon, LIcon, LIconCircular

filename = os.path.join(UIX, "icon", "icon.kv")
if not filename in Builder.files:
    Builder.load_file(filename)
