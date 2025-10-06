# View/PasswordScreen/password_screen.py
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.metrics import dp, sp
from View.base_screen import BaseScreen

class PasswordScreenView(Screen, BaseScreen):
    def __init__(self, controller, **kwargs):
        super().__init__(**kwargs)
        self.controller = controller
        self.app = None
        
        # Main layout
        layout = BoxLayout(orientation='vertical', padding=dp(40), spacing=dp(20))
        
        # Logo/Title
        title_layout = BoxLayout(orientation='vertical', size_hint=(1, 0.3))
        title = Label(
            text='Luna Wallet', 
            font_size=sp(32), 
            bold=True,
            size_hint=(1, 0.6)
        )
        subtitle = Label(
            text='Secure Cryptocurrency Wallet', 
            font_size=sp(16),
            size_hint=(1, 0.4)
        )
        title_layout.add_widget(title)
        title_layout.add_widget(subtitle)
        
        # Password input
        password_layout = BoxLayout(orientation='vertical', size_hint=(1, 0.4), spacing=dp(10))
        password_label = Label(
            text='Enter Password to Unlock Wallet', 
            font_size=sp(18),
            size_hint=(1, 0.3)
        )
        self.password_input = TextInput(
            hint_text='Password',
            password=True,
            multiline=False,
            size_hint=(1, 0.4),
            font_size=sp(18)
        )
        self.error_label = Label(
            text='', 
            font_size=sp(14),
            size_hint=(1, 0.3),
            color=(1, 0.2, 0.2, 1)
        )
        
        password_layout.add_widget(password_label)
        password_layout.add_widget(self.password_input)
        password_layout.add_widget(self.error_label)
        
        # Buttons
        button_layout = BoxLayout(orientation='vertical', size_hint=(1, 0.3), spacing=dp(10))
        unlock_btn = Button(
            text='Unlock Wallet', 
            size_hint=(1, 0.5),
            font_size=sp(18)
        )
        
        unlock_btn.bind(on_press=self.unlock_wallet)
        
        button_layout.add_widget(unlock_btn)
        
        layout.add_widget(title_layout)
        layout.add_widget(password_layout)
        layout.add_widget(button_layout)
        
        self.add_widget(layout)
        
    def on_enter(self):
        """Called when screen becomes active"""
        super().on_enter()
        self.password_input.text = ''
        self.error_label.text = ''
        self.password_input.focus = True
        
    def unlock_wallet(self, instance):
        """Attempt to unlock wallet with password"""
        password = self.password_input.text.strip()
        if not password:
            self.error_label.text = 'Please enter password'
            return
            
        if self.controller.unlock_wallet(password):
            self.manager_screens.current = 'balance'
        else:
            self.error_label.text = 'Invalid password'