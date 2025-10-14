import os

from kivy.lang import Builder

from design.config import UIX

from .button import (
    LButton,
    LButtonDanger,
    LButtonGhost,
    LButtonIcon,
    LButtonLabel,
    LButtonPrimary,
    LButtonSecondary,
    LButtonTertiary,
)

filename = os.path.join(UIX, "button", "button.kv")
if not filename in Builder.files:
    Builder.load_file(filename)
