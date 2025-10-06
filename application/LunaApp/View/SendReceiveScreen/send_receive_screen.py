# View/SendReceiveScreen/send_receive_screen.py
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.metrics import dp, sp
import qrcode
import io
from View.base_screen import BaseScreen

class SendReceiveScreenView(Screen, BaseScreen):
    def __init__(self, controller, **kwargs):
        super().__init__(**kwargs)
        self.controller = controller
        self.app = None
        
        self.layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
        
        # Header
        header = BoxLayout(orientation='horizontal', size_hint=(1, 0.1))
        theme_btn = Button(text='🌙', size_hint=(0.15, 1), font_size=sp(20))
        theme_btn.bind(on_press=self.toggle_theme)
        title = Label(text='Send & Receive', font_size=sp(26), size_hint=(0.85, 1))
        header.add_widget(theme_btn)
        header.add_widget(title)
        
        # QR Code Section
        qr_card = BoxLayout(orientation='vertical', size_hint=(1, 0.35), padding=dp(15))
        
        self.qr_image = Image(size_hint=(1, 0.7))
        self.address_label = Label(
            text='Your Address: Loading...', 
            font_size=sp(14), 
            halign='center'
        )
        
        qr_card.add_widget(self.qr_image)
        qr_card.add_widget(self.address_label)
        
        # Send Section
        send_card = BoxLayout(orientation='vertical', size_hint=(1, 0.55), spacing=dp(10), padding=dp(15))
        
        send_card.add_widget(Label(text='Send LKC', font_size=sp(20), size_hint=(1, 0.15)))
        
        # To Address
        to_layout = BoxLayout(orientation='vertical', size_hint=(1, 0.2))
        to_layout.add_widget(Label(text='To Address:', size_hint=(1, 0.4), font_size=sp(16)))
        self.to_address = TextInput(
            hint_text='LUN_...', 
            multiline=False, 
            size_hint=(1, 0.6),
            font_size=sp(16)
        )
        to_layout.add_widget(self.to_address)
        
        # Amount
        amount_layout = BoxLayout(orientation='vertical', size_hint=(1, 0.2))
        amount_layout.add_widget(Label(text='Amount:', size_hint=(1, 0.4), font_size=sp(16)))
        self.amount_input = TextInput(
            hint_text='0.000000', 
            multiline=False, 
            size_hint=(1, 0.6),
            font_size=sp(16),
            input_type='number'
        )
        amount_layout.add_widget(self.amount_input)
        
        # Memo
        memo_layout = BoxLayout(orientation='vertical', size_hint=(1, 0.2))
        memo_layout.add_widget(Label(text='Memo (optional):', size_hint=(1, 0.4), font_size=sp(16)))
        self.memo_input = TextInput(
            hint_text='Message', 
            multiline=False, 
            size_hint=(1, 0.6),
            font_size=sp(16)
        )
        memo_layout.add_widget(self.memo_input)
        
        # Send Button
        send_btn = Button(text='Send Transaction', size_hint=(1, 0.2), font_size=sp(18))
        send_btn.bind(on_press=self.send_transaction)
        
        send_card.add_widget(to_layout)
        send_card.add_widget(amount_layout)
        send_card.add_widget(memo_layout)
        send_card.add_widget(send_btn)
        
        self.layout.add_widget(header)
        self.layout.add_widget(qr_card)
        self.layout.add_widget(send_card)
        self.add_widget(self.layout)
        
    def on_enter(self):
        """Called when screen becomes active"""
        super().on_enter()
        self.update_data()
        
    def toggle_theme(self, instance):
        if self.app:
            self.app.toggle_theme()
            
    def send_transaction(self, instance):
        to_address = self.to_address.text.strip()
        amount_text = self.amount_input.text.strip()
        memo = self.memo_input.text.strip()
        
        if not to_address or not amount_text:
            self.show_popup("Error", "Please enter address and amount")
            return
            
        try:
            amount = float(amount_text)
            if amount <= 0:
                self.show_popup("Error", "Amount must be positive")
                return
                
            success = self.controller.send_transaction(to_address, amount, memo)
            if success:
                self.show_popup("Success", f"Sent {amount} LKC to {to_address}")
                self.to_address.text = ""
                self.amount_input.text = ""
                self.memo_input.text = ""
            else:
                self.show_popup("Error", "Failed to send transaction")
                
        except ValueError:
            self.show_popup("Error", "Invalid amount")
            
    def show_popup(self, title, message):
        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        content.add_widget(Label(text=message, font_size=sp(16)))
        btn = Button(text='OK', size_hint=(1, 0.3), font_size=sp(16))
        popup = Popup(
            title=title, 
            content=content, 
            size_hint=(0.8, 0.4),
            title_size=sp(18)
        )
        btn.bind(on_press=popup.dismiss)
        content.add_widget(btn)
        popup.open()
        
    def update_data(self):
        """Update screen with wallet data"""
        address = self.controller.get_wallet_address()
        if address:
            self.address_label.text = f'Your Address: {address}'
            self.generate_qr_code(address)
                
    def generate_qr_code(self, address):
        """Generate QR code for address"""
        try:
            qr_data = self.controller.generate_qr_code(address)
            if qr_data:
                self.qr_image.texture = Image(qr_data).texture
            else:
                # Fallback QR generation
                qr = qrcode.QRCode(version=1, box_size=4, border=4)
                qr.add_data(address)
                qr.make(fit=True)
                
                img = qr.make_image(fill_color="black", back_color="white")
                bio = io.BytesIO()
                img.save(bio, format='PNG')
                bio.seek(0)
                self.qr_image.texture = Image(bio).texture
        except Exception as e:
            print(f"QR generation error: {e}")
            
    def update_theme(self):
        """Update colors for theme"""
        if self.theme:
            self.address_label.color = self.theme.TEXT_PRIMARY