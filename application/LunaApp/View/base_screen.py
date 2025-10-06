# View/base_screen.py
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp, sp

class LoadingLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (1, 1)
        self.add_widget(Label(text="Loading...", font_size=sp(24)))

class BaseScreen:
    """Mixin class for all screens with theme support"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.theme = None
        self.app = None
        
    def apply_theme(self, theme):
        """Apply theme to all widgets"""
        self.theme = theme
        Clock.schedule_once(self._update_background, 0)
        self.update_theme()
        
    def _update_background(self, dt):
        """Safely update background"""
        if hasattr(self, 'canvas') and self.theme:
            self.canvas.before.clear()
            with self.canvas.before:
                Color(*self.theme.BACKGROUND)
                Rectangle(pos=self.pos, size=self.size)
        
    def update_theme(self):
        """Update widget colors - to be implemented by subclasses"""
        pass