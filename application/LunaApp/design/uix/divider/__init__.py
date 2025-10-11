import os

from kivy.lang import Builder

from design.config import UIX

from .divider import LDivider

filename = os.path.join(UIX, "divider", "divider.kv")
if not filename in Builder.files:
    Builder.load_file(filename)
