# View/BalanceScreen/balance_screen.py
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.metrics import dp, sp
from View.base_screen import BaseScreen

class BalanceScreenView(Screen, BaseScreen):
    def __init__(self, controller, **kwargs):
        super().__init__(**kwargs)
        self.controller = controller
        self.app = None
        
        self.layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
        
        # Header
        header = BoxLayout(orientation='horizontal', size_hint=(1, 0.12))
        self.sync_indicator = Label(text='🔄', font_size=sp(24), size_hint=(0.15, 1))
        self.theme_toggle = Button(text='🌙', size_hint=(0.15, 1), font_size=sp(20))
        self.theme_toggle.bind(on_press=self.toggle_theme)
        title = Label(text='Wallet Balance', font_size=sp(26), size_hint=(0.7, 1))
        header.add_widget(self.sync_indicator)
        header.add_widget(title)
        header.add_widget(self.theme_toggle)
        
        # Balance Card
        balance_card = BoxLayout(orientation='vertical', size_hint=(1, 0.25), padding=dp(15))
        
        self.balance_label = Label(text='0.000000 LKC', font_size=sp(34), bold=True)
        self.available_label = Label(text='Available: 0.000000 LKC', font_size=sp(18))
        self.pending_label = Label(text='Pending: 0.000000 LKC', font_size=sp(16))
        
        balance_card.add_widget(self.balance_label)
        balance_card.add_widget(self.available_label)
        balance_card.add_widget(self.pending_label)
        
        # Sync Button
        sync_btn = Button(text='Sync Now', size_hint=(1, 0.1), font_size=sp(18))
        sync_btn.bind(on_press=self.sync_wallet)
        
        # Stats
        stats_card = BoxLayout(orientation='vertical', size_hint=(1, 0.4), padding=dp(15))
        
        self.address_label = Label(
            text='Address: Loading...', 
            font_size=sp(14), 
            halign='left', 
            valign='top'
        )
        self.transactions_label = Label(text='Transactions: 0', font_size=sp(16))
        self.wallet_label = Label(text='Wallet: Primary', font_size=sp(16))
        
        stats_card.add_widget(Label(text='Wallet Info', font_size=sp(20), size_hint=(1, 0.2)))
        stats_card.add_widget(self.address_label)
        stats_card.add_widget(self.transactions_label)
        stats_card.add_widget(self.wallet_label)
        
        self.layout.add_widget(header)
        self.layout.add_widget(balance_card)
        self.layout.add_widget(sync_btn)
        self.layout.add_widget(stats_card)
        self.add_widget(self.layout)
        
    def on_enter(self):
        """Called when screen becomes active"""
        super().on_enter()
        self.update_data()
        
    def toggle_theme(self, instance):
        if self.app:
            self.app.toggle_theme()
            
    def sync_wallet(self, instance):
        if self.controller.sync_wallet():
            self.update_data()
            
    def update_data(self):
        """Update screen with wallet data"""
        wallet_info = self.controller.get_wallet_info()
        if wallet_info:
            self.balance_label.text = f'{wallet_info["balance"]:.6f} LKC'
            self.available_label.text = f'Available: {wallet_info["available_balance"]:.6f} LKC'
            self.pending_label.text = f'Pending: {wallet_info["pending_send"]:.6f} LKC'
            self.address_label.text = f'Address: {wallet_info["address"]}'
            self.transactions_label.text = f'Transactions: {wallet_info["transaction_count"]}'
            self.wallet_label.text = f'Wallet: {wallet_info["label"]}'
            
    def update_theme(self):
        """Update colors for theme"""
        if self.theme:
            self.balance_label.color = self.theme.TEXT_PRIMARY
            self.available_label.color = self.theme.TEXT_SECONDARY
            self.pending_label.color = self.theme.WARNING
            self.address_label.color = self.theme.TEXT_PRIMARY
            self.transactions_label.color = self.theme.TEXT_PRIMARY
            self.wallet_label.color = self.theme.TEXT_PRIMARY