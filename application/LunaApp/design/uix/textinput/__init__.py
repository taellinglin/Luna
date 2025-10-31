import os

from kivy.lang import Builder

from design.config import UIX

from .textinput import (
    LTextInput,
    LTextInputHelperText,
    LTextInputLabel,
    LTextInputLayout,
    LTextInputTrailingIconButton,
)

filename = os.path.join(UIX, "textinput", "textinput.kv")
if not filename in Builder.files:
    Builder.load_file(filename)
