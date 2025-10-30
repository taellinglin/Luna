import os

from kivy.lang import Builder

from design.config import UIX

from .link import LLink, LLinkIcon, LLinkText

filename = os.path.join(UIX, "link", "link.kv")
if not filename in Builder.files:
    Builder.load_file(filename)
