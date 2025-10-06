# View/SetupScreen/setup_screen.py
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.metrics import dp, sp
from View.base_screen import BaseScreen

class SetupScreenView(Screen, BaseScreen):
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
        
        # Setup options
        options_layout = BoxLayout(orientation='vertical', size_hint=(1, 0.6), spacing=dp(15))
        
        create_btn = Button(
            text='Create New Wallet', 
            size_hint=(1, 0.4),
            font_size=sp(18)
        )
        restore_btn = Button(
            text='Restore Existing Wallet', 
            size_hint=(1, 0.4),
            font_size=sp(18)
        )
        
        create_btn.bind(on_press=self.create_new_wallet)
        restore_btn.bind(on_press=self.restore_wallet)
        
        options_layout.add_widget(create_btn)
        options_layout.add_widget(restore_btn)
        
        layout.add_widget(title_layout)
        layout.add_widget(options_layout)
        self.add_widget(layout)
        
    def create_new_wallet(self, instance):
        """Show password setup for new wallet"""
        content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
        content.add_widget(Label(text='Set Wallet Password', font_size=sp(20)))
        
        password_input = TextInput(
            hint_text='Password',
            password=True,
            multiline=False,
            size_hint=(1, 0.3),
            font_size=sp(18)
        )
        confirm_input = TextInput(
            hint_text='Confirm Password',
            password=True,
            multiline=False,
            size_hint=(1, 0.3),
            font_size=sp(18)
        )
        error_label = Label(
            text='', 
            font_size=sp(14),
            size_hint=(1, 0.2),
            color=(1, 0.2, 0.2, 1)
        )
        
        btn_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.2), spacing=dp(10))
        create_btn = Button(text='Create Wallet', font_size=sp(16))
        cancel_btn = Button(text='Cancel', font_size=sp(16))
        
        content.add_widget(password_input)
        content.add_widget(confirm_input)
        content.add_widget(error_label)
        content.add_widget(btn_layout)
        
        popup = Popup(
            title='Create New Wallet', 
            content=content, 
            size_hint=(0.9, 0.6),
            title_size=sp(18)
        )
        
        def do_create(btn):
            password = password_input.text.strip()
            confirm = confirm_input.text.strip()
            
            if not password:
                error_label.text = 'Please enter password'
                return
            if password != confirm:
                error_label.text = 'Passwords do not match'
                return
            if len(password) < 4:
                error_label.text = 'Password too short (min 4 chars)'
                return
                
            if self.controller.create_wallet(password):
                popup.dismiss()
                self.manager_screens.current = 'balance'
            else:
                error_label.text = 'Failed to create wallet'
            
        create_btn.bind(on_press=do_create)
        cancel_btn.bind(on_press=popup.dismiss)
        
        btn_layout.add_widget(create_btn)
        btn_layout.add_widget(cancel_btn)
        popup.open()
        
    def restore_wallet(self, instance):
        """Show restore wallet options"""
        content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
        content.add_widget(Label(text='Restore Wallet', font_size=sp(20)))
        
        private_key_input = TextInput(
            hint_text='Private Key (64 hex characters)',
            multiline=False,
            size_hint=(1, 0.3),
            font_size=sp(16)
        )
        password_input = TextInput(
            hint_text='Set New Password',
            password=True,
            multiline=False,
            size_hint=(1, 0.3),
            font_size=sp(18)
        )
        error_label = Label(
            text='', 
            font_size=sp(14),
            size_hint=(1, 0.2),
            color=(1, 0.2, 0.2, 1)
        )
        
        btn_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.2), spacing=dp(10))
        restore_btn = Button(text='Restore Wallet', font_size=sp(16))
        cancel_btn = Button(text='Cancel', font_size=sp(16))
        
        content.add_widget(private_key_input)
        content.add_widget(password_input)
        content.add_widget(error_label)
        content.add_widget(btn_layout)
        
        popup = Popup(
            title='Restore Wallet', 
            content=content, 
            size_hint=(0.9, 0.6),
            title_size=sp(18)
        )
        
        def do_restore(btn):
            private_key = private_key_input.text.strip()
            password = password_input.text.strip()
            
            if not private_key or len(private_key) != 64:
                error_label.text = 'Invalid private key (must be 64 hex chars)'
                return
            if not password:
                error_label.text = 'Please enter password'
                return
                
            if self.controller.restore_wallet(private_key, password):
                popup.dismiss()
                self.manager_screens.current = 'balance'
            else:
                error_label.text = 'Failed to restore wallet'
            
        restore_btn.bind(on_press=do_restore)
        cancel_btn.bind(on_press=popup.dismiss)
        
        btn_layout.add_widget(restore_btn)
        btn_layout.add_widget(cancel_btn)
        popup.open()