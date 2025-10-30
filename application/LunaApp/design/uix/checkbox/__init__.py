import os

from kivy.lang import Builder

from design.config import UIX

from .checkbox import LCheckbox

filename = os.path.join(UIX, "checkbox", "checkbox.kv")
if not filename in Builder.files:
    Builder.load_file(filename)
