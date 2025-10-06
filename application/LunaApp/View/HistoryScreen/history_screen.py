# View/HistoryScreen/history_screen.py
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.metrics import dp, sp
from View.base_screen import BaseScreen

class HistoryScreenView(Screen, BaseScreen):
    def __init__(self, controller, **kwargs):
        super().__init__(**kwargs)
        self.controller = controller
        self.app = None
        
        self.layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
        
        # Header
        header = BoxLayout(orientation='horizontal', size_hint=(1, 0.1))
        theme_btn = Button(text='🌙', size_hint=(0.15, 1), font_size=sp(20))
        theme_btn.bind(on_press=self.toggle_theme)
        title = Label(text='Transaction History', font_size=sp(26), size_hint=(0.85, 1))
        header.add_widget(theme_btn)
        header.add_widget(title)
        
        # Action Buttons
        action_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.12), spacing=dp(10))
        import_btn = Button(text='Import', font_size=sp(16))
        export_btn = Button(text='Export', font_size=sp(16))
        new_btn = Button(text='New Wallet', font_size=sp(16))
        
        import_btn.bind(on_press=self.import_wallet)
        export_btn.bind(on_press=self.export_wallet)
        new_btn.bind(on_press=self.new_wallet)
        
        action_layout.add_widget(import_btn)
        action_layout.add_widget(export_btn)
        action_layout.add_widget(new_btn)
        
        # Transaction History
        history_scroll = ScrollView(size_hint=(1, 0.78))
        self.history_layout = GridLayout(cols=1, spacing=dp(10), size_hint_y=None)
        self.history_layout.bind(minimum_height=self.history_layout.setter('height'))
        
        history_scroll.add_widget(self.history_layout)
        
        self.layout.add_widget(header)
        self.layout.add_widget(action_layout)
        self.layout.add_widget(history_scroll)
        self.add_widget(self.layout)
        
    def on_enter(self):
        """Called when screen becomes active"""
        super().on_enter()
        self.update_data()
        
    def toggle_theme(self, instance):
        if self.app:
            self.app.toggle_theme()
            
    def import_wallet(self, instance):
        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10), size_hint_y=None)
        content.add_widget(Label(text='Import Wallet from Private Key', font_size=sp(18)))
        
        private_key_input = TextInput(
            hint_text='Enter private key (64 hex chars)', 
            multiline=False, 
            size_hint_y=None, 
            height=dp(50),
            font_size=sp(16)
        )
        label_input = TextInput(
            hint_text='Wallet label (optional)', 
            multiline=False, 
            size_hint_y=None, 
            height=dp(50),
            font_size=sp(16)
        )
        
        btn_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50), spacing=dp(10))
        import_btn = Button(text='Import', font_size=sp(16))
        cancel_btn = Button(text='Cancel', font_size=sp(16))
        
        content.add_widget(private_key_input)
        content.add_widget(label_input)
        content.add_widget(btn_layout)
        
        popup = Popup(
            title='Import Wallet', 
            content=content, 
            size_hint=(0.9, 0.6),
            title_size=sp(18)
        )
        
        def do_import(btn):
            private_key = private_key_input.text.strip()
            label = label_input.text.strip()
            if private_key and self.controller.import_wallet(private_key, label):
                self.show_popup("Success", "Wallet imported successfully")
                self.update_data()
            else:
                self.show_popup("Error", "Failed to import wallet")
            popup.dismiss()
            
        import_btn.bind(on_press=do_import)
        cancel_btn.bind(on_press=popup.dismiss)
        
        btn_layout.add_widget(import_btn)
        btn_layout.add_widget(cancel_btn)
        popup.open()
        
    def export_wallet(self, instance):
        wallet_data = self.controller.export_wallet()
        if wallet_data:
            content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
            content.add_widget(Label(text='PRIVATE KEY EXPORT', font_size=sp(16), bold=True))
            content.add_widget(Label(text=f"Address: {wallet_data['address']}", font_size=sp(14)))
            content.add_widget(Label(text=f"Private Key: {wallet_data['private_key']}", font_size=sp(12)))
            content.add_widget(Label(text="⚠️ KEEP THIS SECURE! NEVER SHARE!", font_size=sp(12), color=(1, 0, 0, 1)))
            
            btn = Button(text='OK', size_hint=(1, 0.2))
            popup = Popup(
                title='Wallet Export', 
                content=content, 
                size_hint=(0.9, 0.5),
                title_size=sp(18)
            )
            btn.bind(on_press=popup.dismiss)
            content.add_widget(btn)
            popup.open()
        else:
            self.show_popup("Error", "Failed to export wallet")
            
    def new_wallet(self, instance):
        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10), size_hint_y=None)
        content.add_widget(Label(text='Create New Wallet', font_size=sp(18)))
        
        label_input = TextInput(
            hint_text='Wallet label', 
            multiline=False, 
            size_hint_y=None, 
            height=dp(50),
            font_size=sp(16)
        )
        
        btn_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50), spacing=dp(10))
        create_btn = Button(text='Create', font_size=sp(16))
        cancel_btn = Button(text='Cancel', font_size=sp(16))
        
        content.add_widget(label_input)
        content.add_widget(btn_layout)
        
        popup = Popup(
            title='New Wallet', 
            content=content, 
            size_hint=(0.8, 0.4),
            title_size=sp(18)
        )
        
        def do_create(btn):
            label = label_input.text.strip() or "New Wallet"
            address = self.controller.create_wallet(label)
            if address:
                self.show_popup("Success", f"Wallet '{label}' created")
                self.update_data()
            else:
                self.show_popup("Error", "Failed to create wallet")
            popup.dismiss()
            
        create_btn.bind(on_press=do_create)
        cancel_btn.bind(on_press=popup.dismiss)
        
        btn_layout.add_widget(create_btn)
        btn_layout.add_widget(cancel_btn)
        popup.open()
        
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
        """Update transaction history"""
        self.history_layout.clear_widgets()
        self.history_layout.height = 0
        
        transactions = self.controller.get_transaction_history()
        
        if not transactions:
            no_tx_label = Label(
                text='No transactions found', 
                size_hint_y=None, 
                height=dp(60),
                font_size=sp(16)
            )
            self.history_layout.add_widget(no_tx_label)
            return
            
        for tx in transactions:
            tx_card = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(70))
            
            # Type icon
            tx_type = tx.get('type', 'transfer')
            if tx_type == 'reward':
                icon = '💰'
                color = (0.2, 0.8, 0.2, 1) if self.theme else (0.2, 0.8, 0.2, 1)
            else:
                from_addr = tx.get('from', '')
                wallet_addr = tx.get('wallet_address', '')
                if from_addr == wallet_addr:
                    icon = '➡️'
                    color = (0.8, 0.6, 0.2, 1) if self.theme else (0.8, 0.6, 0.2, 1)
                else:
                    icon = '⬅️'
                    color = (0.2, 0.8, 0.2, 1) if self.theme else (0.2, 0.8, 0.2, 1)
                    
            # Status
            status = tx.get('status', 'unknown')
            if status == 'confirmed':
                status_icon = '✅'
            elif status == 'pending':
                status_icon = '⏳'
            else:
                status_icon = '❓'
                
            icon_label = Label(
                text=f'{icon} {status_icon}', 
                size_hint=(0.2, 1),
                font_size=sp(20)
            )
            icon_label.color = color
            
            # Details
            details_layout = BoxLayout(orientation='vertical', size_hint=(0.8, 1))
            amount = tx.get('amount', 0)
            amount_label = Label(
                text=f'{amount:.6f} LKC', 
                size_hint=(1, 0.5), 
                halign='left',
                font_size=sp(16)
            )
            amount_label.color = self.theme.TEXT_PRIMARY if self.theme else (1, 1, 1, 1)
            
            from_to = f"From: {tx.get('from', 'Network')}" if tx_type != 'reward' else "Mining Reward"
            from_label = Label(
                text=from_to, 
                font_size=sp(12), 
                size_hint=(1, 0.5), 
                halign='left'
            )
            from_label.color = self.theme.TEXT_SECONDARY if self.theme else (0.7, 0.7, 0.7, 1)
            
            details_layout.add_widget(amount_label)
            details_layout.add_widget(from_label)
            
            tx_card.add_widget(icon_label)
            tx_card.add_widget(details_layout)
            self.history_layout.add_widget(tx_card)
            
    def update_theme(self):
        """Update colors for theme"""
        pass