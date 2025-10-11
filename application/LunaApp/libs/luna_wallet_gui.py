#!/usr/bin/env python3
"""
Luna Wallet - Kivy GUI Version - Mobile Optimized
Using the new LunaWallet library (Fixed Version)
"""

import os
import sys
import threading
from kivy.config import Config

# Remove fixed size to allow responsive design
Config.set("graphics", "resizable", "1")
import qrcode
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.utils import platform
import qrcode
import io

# Import the new LunaWallet library
from application.LunaApp.libs.luna_wallet_lib import LunaWallet


class DarkTheme:
    """Dark theme colors (Black and Red)"""

    BACKGROUND = [0.1, 0.1, 0.1, 1]  # Dark background
    CARD_BG = [0.2, 0.2, 0.2, 1]  # Card background
    TEXT_PRIMARY = [1, 1, 1, 1]  # White text
    TEXT_SECONDARY = [0.7, 0.7, 0.7, 1]  # Gray text
    ACCENT = [0.8, 0.2, 0.2, 1]  # Red accent
    SUCCESS = [0.2, 0.8, 0.2, 1]  # Green for success
    WARNING = [0.8, 0.6, 0.2, 1]  # Yellow/orange for warnings


class LightTheme:
    """Light theme colors (White and Blue)"""

    BACKGROUND = [0.95, 0.95, 0.95, 1]  # Light background
    CARD_BG = [1, 1, 1, 1]  # White card background
    TEXT_PRIMARY = [0.1, 0.1, 0.1, 1]  # Dark text
    TEXT_SECONDARY = [0.4, 0.4, 0.4, 1]  # Gray text
    ACCENT = [0.2, 0.4, 0.8, 1]  # Blue accent
    SUCCESS = [0.2, 0.6, 0.2, 1]  # Green for success
    WARNING = [0.8, 0.5, 0.1, 1]  # Orange for warnings


class BaseScreen(Screen):
    """Base class for all screens with theme support"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.theme = DarkTheme()
        self.app = None

    def apply_theme(self, theme):
        """Apply theme to all widgets"""
        self.theme = theme
        # Use Clock to safely update background
        Clock.schedule_once(self._update_background, 0)
        self.update_theme()

    def _update_background(self, dt):
        """Safely update background"""
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.theme.BACKGROUND)
            Rectangle(pos=self.pos, size=self.size)

    def update_theme(self):
        """Update widget colors - to be implemented by subclasses"""
        pass


class SetupScreen(BaseScreen):
    """Initial setup screen for new users"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Main layout
        layout = BoxLayout(orientation="vertical", padding=dp(40), spacing=dp(20))

        # Logo/Title
        title_layout = BoxLayout(orientation="vertical", size_hint=(1, 0.3))
        title = Label(
            text="Luna Wallet", font_size=sp(32), bold=True, size_hint=(1, 0.6)
        )
        subtitle = Label(
            text="Secure Cryptocurrency Wallet", font_size=sp(16), size_hint=(1, 0.4)
        )
        title_layout.add_widget(title)
        title_layout.add_widget(subtitle)

        # Setup options
        options_layout = BoxLayout(
            orientation="vertical", size_hint=(1, 0.6), spacing=dp(15)
        )

        create_btn = Button(
            text="Create New Wallet", size_hint=(1, 0.4), font_size=sp(18)
        )
        restore_btn = Button(
            text="Restore Existing Wallet", size_hint=(1, 0.4), font_size=sp(18)
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
        content = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(15))
        content.add_widget(Label(text="Set Wallet Password", font_size=sp(20)))

        password_input = TextInput(
            hint_text="Password",
            password=True,
            multiline=False,
            size_hint=(1, 0.3),
            font_size=sp(18),
        )
        confirm_input = TextInput(
            hint_text="Confirm Password",
            password=True,
            multiline=False,
            size_hint=(1, 0.3),
            font_size=sp(18),
        )
        error_label = Label(
            text="", font_size=sp(14), size_hint=(1, 0.2), color=(1, 0.2, 0.2, 1)
        )

        btn_layout = BoxLayout(
            orientation="horizontal", size_hint=(1, 0.2), spacing=dp(10)
        )
        create_btn = Button(text="Create Wallet", font_size=sp(16))
        cancel_btn = Button(text="Cancel", font_size=sp(16))

        content.add_widget(password_input)
        content.add_widget(confirm_input)
        content.add_widget(error_label)
        content.add_widget(btn_layout)

        popup = Popup(
            title="Create New Wallet",
            content=content,
            size_hint=(0.9, 0.6),
            title_size=sp(18),
        )

        def do_create(btn):
            password = password_input.text.strip()
            confirm = confirm_input.text.strip()

            if not password:
                error_label.text = "Please enter password"
                return
            if password != confirm:
                error_label.text = "Passwords do not match"
                return
            if len(password) < 4:
                error_label.text = "Password too short (min 4 chars)"
                return

            if self.app and self.app.initialize_wallet(password):
                popup.dismiss()
                self.manager.current = "main"
            else:
                error_label.text = "Failed to create wallet"

        create_btn.bind(on_press=do_create)
        cancel_btn.bind(on_press=popup.dismiss)

        btn_layout.add_widget(create_btn)
        btn_layout.add_widget(cancel_btn)
        popup.open()

    def restore_wallet(self, instance):
        """Show restore wallet options"""
        content = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(15))
        content.add_widget(Label(text="Restore Wallet", font_size=sp(20)))

        private_key_input = TextInput(
            hint_text="Private Key (64 hex characters)",
            multiline=False,
            size_hint=(1, 0.3),
            font_size=sp(16),
        )
        password_input = TextInput(
            hint_text="Set New Password",
            password=True,
            multiline=False,
            size_hint=(1, 0.3),
            font_size=sp(18),
        )
        error_label = Label(
            text="", font_size=sp(14), size_hint=(1, 0.2), color=(1, 0.2, 0.2, 1)
        )

        btn_layout = BoxLayout(
            orientation="horizontal", size_hint=(1, 0.2), spacing=dp(10)
        )
        restore_btn = Button(text="Restore Wallet", font_size=sp(16))
        cancel_btn = Button(text="Cancel", font_size=sp(16))

        content.add_widget(private_key_input)
        content.add_widget(password_input)
        content.add_widget(error_label)
        content.add_widget(btn_layout)

        popup = Popup(
            title="Restore Wallet",
            content=content,
            size_hint=(0.9, 0.6),
            title_size=sp(18),
        )

        def do_restore(btn):
            private_key = private_key_input.text.strip()
            password = password_input.text.strip()

            if not private_key or len(private_key) != 64:
                error_label.text = "Invalid private key (must be 64 hex chars)"
                return
            if not password:
                error_label.text = "Please enter password"
                return

            if self.app and self.app.restore_wallet(private_key, password):
                popup.dismiss()
                self.manager.current = "main"
            else:
                error_label.text = "Failed to restore wallet"

        restore_btn.bind(on_press=do_restore)
        cancel_btn.bind(on_press=popup.dismiss)

        btn_layout.add_widget(restore_btn)
        btn_layout.add_widget(cancel_btn)
        popup.open()


class PasswordScreen(BaseScreen):
    """Password entry screen for wallet security"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Main layout
        layout = BoxLayout(orientation="vertical", padding=dp(40), spacing=dp(20))

        # Logo/Title
        title_layout = BoxLayout(orientation="vertical", size_hint=(1, 0.3))
        title = Label(
            text="Luna Wallet", font_size=sp(32), bold=True, size_hint=(1, 0.6)
        )
        subtitle = Label(
            text="Secure Cryptocurrency Wallet", font_size=sp(16), size_hint=(1, 0.4)
        )
        title_layout.add_widget(title)
        title_layout.add_widget(subtitle)

        # Password input
        password_layout = BoxLayout(
            orientation="vertical", size_hint=(1, 0.4), spacing=dp(10)
        )
        password_label = Label(
            text="Enter Password to Unlock Wallet", font_size=sp(18), size_hint=(1, 0.3)
        )
        self.password_input = TextInput(
            hint_text="Password",
            password=True,
            multiline=False,
            size_hint=(1, 0.4),
            font_size=sp(18),
        )
        self.error_label = Label(
            text="", font_size=sp(14), size_hint=(1, 0.3), color=(1, 0.2, 0.2, 1)
        )

        password_layout.add_widget(password_label)
        password_layout.add_widget(self.password_input)
        password_layout.add_widget(self.error_label)

        # Buttons
        button_layout = BoxLayout(
            orientation="vertical", size_hint=(1, 0.3), spacing=dp(10)
        )
        unlock_btn = Button(text="Unlock Wallet", size_hint=(1, 0.5), font_size=sp(18))

        unlock_btn.bind(on_press=self.unlock_wallet)

        button_layout.add_widget(unlock_btn)

        layout.add_widget(title_layout)
        layout.add_widget(password_layout)
        layout.add_widget(button_layout)

        self.add_widget(layout)

    def on_enter(self):
        """Called when screen becomes active"""
        super().on_enter()
        self.password_input.text = ""
        self.error_label.text = ""
        self.password_input.focus = True

    def unlock_wallet(self, instance):
        """Attempt to unlock wallet with password"""
        password = self.password_input.text.strip()
        if not password:
            self.error_label.text = "Please enter password"
            return

        if self.app and self.app.unlock_wallet(password):
            self.manager.current = "main"
        else:
            self.error_label.text = "Invalid password"


class BalanceScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(15))

        # Header
        header = BoxLayout(orientation="horizontal", size_hint=(1, 0.12))
        self.sync_indicator = Label(text="🔄", font_size=sp(24), size_hint=(0.15, 1))
        self.theme_toggle = Button(text="🌙", size_hint=(0.15, 1), font_size=sp(20))
        self.theme_toggle.bind(on_press=self.toggle_theme)
        title = Label(text="Wallet Balance", font_size=sp(26), size_hint=(0.7, 1))
        header.add_widget(self.sync_indicator)
        header.add_widget(title)
        header.add_widget(self.theme_toggle)

        # Balance Card
        balance_card = BoxLayout(
            orientation="vertical", size_hint=(1, 0.25), padding=dp(15)
        )

        self.balance_label = Label(text="0.000000 LKC", font_size=sp(34), bold=True)
        self.available_label = Label(text="Available: 0.000000 LKC", font_size=sp(18))
        self.pending_label = Label(text="Pending: 0.000000 LKC", font_size=sp(16))

        balance_card.add_widget(self.balance_label)
        balance_card.add_widget(self.available_label)
        balance_card.add_widget(self.pending_label)

        # Sync Button
        sync_btn = Button(text="Sync Now", size_hint=(1, 0.1), font_size=sp(18))
        sync_btn.bind(on_press=self.sync_wallet)

        # Stats
        stats_card = BoxLayout(
            orientation="vertical", size_hint=(1, 0.4), padding=dp(15)
        )

        self.address_label = Label(
            text="Address: Loading...", font_size=sp(14), halign="left", valign="top"
        )
        self.transactions_label = Label(text="Transactions: 0", font_size=sp(16))
        self.wallet_label = Label(text="Wallet: Primary", font_size=sp(16))

        stats_card.add_widget(
            Label(text="Wallet Info", font_size=sp(20), size_hint=(1, 0.2))
        )
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
        if self.app:
            self.app.sync_wallet()

    def update_data(self):
        """Update screen with wallet data"""
        if self.app and self.app.wallet and self.app.wallet.is_unlocked:
            wallet_info = self.app.wallet.get_wallet_info()
            if wallet_info:
                self.balance_label.text = f'{wallet_info["balance"]:.6f} LKC'
                self.available_label.text = (
                    f'Available: {wallet_info["available_balance"]:.6f} LKC'
                )
                self.pending_label.text = (
                    f'Pending: {wallet_info["pending_send"]:.6f} LKC'
                )
                self.address_label.text = f'Address: {wallet_info["address"]}'
                self.transactions_label.text = (
                    f'Transactions: {wallet_info["transaction_count"]}'
                )
                self.wallet_label.text = f'Wallet: {wallet_info["label"]}'

    def update_theme(self):
        """Update colors for theme"""
        self.balance_label.color = self.theme.TEXT_PRIMARY
        self.available_label.color = self.theme.TEXT_SECONDARY
        self.pending_label.color = self.theme.WARNING
        self.address_label.color = self.theme.TEXT_PRIMARY
        self.transactions_label.color = self.theme.TEXT_PRIMARY
        self.wallet_label.color = self.theme.TEXT_PRIMARY


class HistoryScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(15))

        # Header
        header = BoxLayout(orientation="horizontal", size_hint=(1, 0.1))
        theme_btn = Button(text="🌙", size_hint=(0.15, 1), font_size=sp(20))
        theme_btn.bind(on_press=self.toggle_theme)
        title = Label(text="Transaction History", font_size=sp(26), size_hint=(0.85, 1))
        header.add_widget(theme_btn)
        header.add_widget(title)

        # Action Buttons
        action_layout = BoxLayout(
            orientation="horizontal", size_hint=(1, 0.12), spacing=dp(10)
        )
        import_btn = Button(text="Import", font_size=sp(16))
        export_btn = Button(text="Export", font_size=sp(16))
        new_btn = Button(text="New Wallet", font_size=sp(16))

        import_btn.bind(on_press=self.import_wallet)
        export_btn.bind(on_press=self.export_wallet)
        new_btn.bind(on_press=self.new_wallet)

        action_layout.add_widget(import_btn)
        action_layout.add_widget(export_btn)
        action_layout.add_widget(new_btn)

        # Transaction History
        history_scroll = ScrollView(size_hint=(1, 0.78))
        self.history_layout = GridLayout(cols=1, spacing=dp(10), size_hint_y=None)
        self.history_layout.bind(minimum_height=self.history_layout.setter("height"))

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
        content = BoxLayout(
            orientation="vertical", padding=dp(10), spacing=dp(10), size_hint_y=None
        )
        content.add_widget(
            Label(text="Import Wallet from Private Key", font_size=sp(18))
        )

        private_key_input = TextInput(
            hint_text="Enter private key (64 hex chars)",
            multiline=False,
            size_hint_y=None,
            height=dp(50),
            font_size=sp(16),
        )
        label_input = TextInput(
            hint_text="Wallet label (optional)",
            multiline=False,
            size_hint_y=None,
            height=dp(50),
            font_size=sp(16),
        )

        btn_layout = BoxLayout(
            orientation="horizontal", size_hint_y=None, height=dp(50), spacing=dp(10)
        )
        import_btn = Button(text="Import", font_size=sp(16))
        cancel_btn = Button(text="Cancel", font_size=sp(16))

        content.add_widget(private_key_input)
        content.add_widget(label_input)
        content.add_widget(btn_layout)

        popup = Popup(
            title="Import Wallet",
            content=content,
            size_hint=(0.9, 0.6),
            title_size=sp(18),
        )

        def do_import(btn):
            private_key = private_key_input.text.strip()
            label = label_input.text.strip()
            if private_key and self.app and self.app.wallet:
                success = self.app.wallet.import_wallet(private_key, label)
                if success:
                    self.show_popup("Success", "Wallet imported successfully")
                    self.app.update_all_screens()
                else:
                    self.show_popup("Error", "Failed to import wallet")
            popup.dismiss()

        import_btn.bind(on_press=do_import)
        cancel_btn.bind(on_press=popup.dismiss)

        btn_layout.add_widget(import_btn)
        btn_layout.add_widget(cancel_btn)
        popup.open()

    def export_wallet(self, instance):
        if self.app and self.app.wallet:
            wallet_data = self.app.wallet.export_wallet()
            if wallet_data:
                content = BoxLayout(
                    orientation="vertical", padding=dp(10), spacing=dp(10)
                )
                content.add_widget(
                    Label(text="PRIVATE KEY EXPORT", font_size=sp(16), bold=True)
                )
                content.add_widget(
                    Label(text=f"Address: {wallet_data['address']}", font_size=sp(14))
                )
                content.add_widget(
                    Label(
                        text=f"Private Key: {wallet_data['private_key']}",
                        font_size=sp(12),
                    )
                )
                content.add_widget(
                    Label(
                        text="⚠️ KEEP THIS SECURE! NEVER SHARE!",
                        font_size=sp(12),
                        color=(1, 0, 0, 1),
                    )
                )

                btn = Button(text="OK", size_hint=(1, 0.2))
                popup = Popup(
                    title="Wallet Export",
                    content=content,
                    size_hint=(0.9, 0.5),
                    title_size=sp(18),
                )
                btn.bind(on_press=popup.dismiss)
                content.add_widget(btn)
                popup.open()
            else:
                self.show_popup("Error", "Failed to export wallet")

    def new_wallet(self, instance):
        content = BoxLayout(
            orientation="vertical", padding=dp(10), spacing=dp(10), size_hint_y=None
        )
        content.add_widget(Label(text="Create New Wallet", font_size=sp(18)))

        label_input = TextInput(
            hint_text="Wallet label",
            multiline=False,
            size_hint_y=None,
            height=dp(50),
            font_size=sp(16),
        )

        btn_layout = BoxLayout(
            orientation="horizontal", size_hint_y=None, height=dp(50), spacing=dp(10)
        )
        create_btn = Button(text="Create", font_size=sp(16))
        cancel_btn = Button(text="Cancel", font_size=sp(16))

        content.add_widget(label_input)
        content.add_widget(btn_layout)

        popup = Popup(
            title="New Wallet", content=content, size_hint=(0.8, 0.4), title_size=sp(18)
        )

        def do_create(btn):
            label = label_input.text.strip() or "New Wallet"
            if self.app and self.app.wallet:
                address = self.app.wallet.create_wallet(label)
                if address:
                    self.app.wallet.save_wallet()
                    self.show_popup("Success", f"Wallet '{label}' created")
                    self.app.update_all_screens()
                else:
                    self.show_popup("Error", "Failed to create wallet")
            popup.dismiss()

        create_btn.bind(on_press=do_create)
        cancel_btn.bind(on_press=popup.dismiss)

        btn_layout.add_widget(create_btn)
        btn_layout.add_widget(cancel_btn)
        popup.open()

    def show_popup(self, title, message):
        content = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10))
        content.add_widget(Label(text=message, font_size=sp(16)))
        btn = Button(text="OK", size_hint=(1, 0.3), font_size=sp(16))
        popup = Popup(
            title=title, content=content, size_hint=(0.8, 0.4), title_size=sp(18)
        )
        btn.bind(on_press=popup.dismiss)
        content.add_widget(btn)
        popup.open()

    def update_data(self):
        """Update transaction history"""
        self.history_layout.clear_widgets()
        self.history_layout.height = 0

        if not self.app or not self.app.wallet or not self.app.wallet.is_unlocked:
            no_tx_label = Label(
                text="No wallet loaded",
                size_hint_y=None,
                height=dp(60),
                font_size=sp(16),
            )
            self.history_layout.add_widget(no_tx_label)
            return

        transactions = self.app.wallet.get_transaction_history()

        if not transactions:
            no_tx_label = Label(
                text="No transactions found",
                size_hint_y=None,
                height=dp(60),
                font_size=sp(16),
            )
            self.history_layout.add_widget(no_tx_label)
            return

        for tx in transactions:
            tx_card = BoxLayout(
                orientation="horizontal", size_hint_y=None, height=dp(70)
            )

            # Type icon
            tx_type = tx.get("type", "transfer")
            if tx_type == "reward":
                icon = "💰"
                color = self.theme.SUCCESS
            else:
                from_addr = tx.get("from", "")
                wallet_addr = tx.get("wallet_address", "")
                if from_addr == wallet_addr:
                    icon = "➡️"
                    color = self.theme.WARNING
                else:
                    icon = "⬅️"
                    color = self.theme.SUCCESS

            # Status
            status = tx.get("status", "unknown")
            if status == "confirmed":
                status_icon = "✅"
            elif status == "pending":
                status_icon = "⏳"
            else:
                status_icon = "❓"

            icon_label = Label(
                text=f"{icon} {status_icon}", size_hint=(0.2, 1), font_size=sp(20)
            )
            icon_label.color = color

            # Details
            details_layout = BoxLayout(orientation="vertical", size_hint=(0.8, 1))
            amount = tx.get("amount", 0)
            amount_label = Label(
                text=f"{amount:.6f} LKC",
                size_hint=(1, 0.5),
                halign="left",
                font_size=sp(16),
            )
            amount_label.color = self.theme.TEXT_PRIMARY

            from_to = (
                f"From: {tx.get('from', 'Network')}"
                if tx_type != "reward"
                else "Mining Reward"
            )
            from_label = Label(
                text=from_to, font_size=sp(12), size_hint=(1, 0.5), halign="left"
            )
            from_label.color = self.theme.TEXT_SECONDARY

            details_layout.add_widget(amount_label)
            details_layout.add_widget(from_label)

            tx_card.add_widget(icon_label)
            tx_card.add_widget(details_layout)
            self.history_layout.add_widget(tx_card)

    def update_theme(self):
        """Update colors for theme"""
        pass


class BottomNav(BoxLayout):
    def __init__(self, screen_manager, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint = (1, 0.1)
        self.screen_manager = screen_manager

        self.balance_btn = Button(text="💰 Balance", font_size=sp(16))
        self.send_btn = Button(text="🔄 Send/Receive", font_size=sp(16))
        self.history_btn = Button(text="📊 History", font_size=sp(16))

        self.balance_btn.bind(on_press=self.switch_to_balance)
        self.send_btn.bind(on_press=self.switch_to_send)
        self.history_btn.bind(on_press=self.switch_to_history)

        self.add_widget(self.balance_btn)
        self.add_widget(self.send_btn)
        self.add_widget(self.history_btn)

    def switch_to_balance(self, instance):
        self.screen_manager.current = "balance"

    def switch_to_send(self, instance):
        self.screen_manager.current = "send_receive"

    def switch_to_history(self, instance):
        self.screen_manager.current = "history"


class MainScreen(BaseScreen):
    """Main screen container for the wallet functionality"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical")
        self.app = None

        # Create screen manager for main app
        self.screen_manager = ScreenManager()

        # Create screens
        self.balance_screen = BalanceScreen(name="balance")
        self.send_receive_screen = SendReceiveScreen(name="send_receive")
        self.history_screen = HistoryScreen(name="history")

        # Set app reference
        self.balance_screen.app = self.app
        self.send_receive_screen.app = self.app
        self.history_screen.app = self.app

        # Add screens to manager
        self.screen_manager.add_widget(self.balance_screen)
        self.screen_manager.add_widget(self.send_receive_screen)
        self.screen_manager.add_widget(self.history_screen)

        # Create bottom navigation
        self.bottom_nav = BottomNav(self.screen_manager)

        self.layout.add_widget(self.screen_manager)
        self.layout.add_widget(self.bottom_nav)
        self.add_widget(self.layout)

    def on_enter(self):
        """Called when screen becomes active"""
        super().on_enter()
        # Update app references when screen becomes active
        for screen in self.screen_manager.screens:
            screen.app = self.app


class SendReceiveScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(15))

        # Header
        header = BoxLayout(orientation="horizontal", size_hint=(1, 0.1))
        theme_btn = Button(text="🌙", size_hint=(0.15, 1), font_size=sp(20))
        theme_btn.bind(on_press=self.toggle_theme)
        title = Label(text="Send & Receive", font_size=sp(26), size_hint=(0.85, 1))
        header.add_widget(theme_btn)
        header.add_widget(title)

        # QR Code Section
        qr_card = BoxLayout(orientation="vertical", size_hint=(1, 0.35), padding=dp(15))

        self.qr_image = Image(size_hint=(1, 0.7))
        self.address_label = Label(
            text="Your Address: Loading...", font_size=sp(14), halign="center"
        )

        qr_card.add_widget(self.qr_image)
        qr_card.add_widget(self.address_label)

        # Send Section
        send_card = BoxLayout(
            orientation="vertical", size_hint=(1, 0.55), spacing=dp(10), padding=dp(15)
        )

        send_card.add_widget(
            Label(text="Send LKC", font_size=sp(20), size_hint=(1, 0.15))
        )

        # To Address
        to_layout = BoxLayout(orientation="vertical", size_hint=(1, 0.2))
        to_layout.add_widget(
            Label(text="To Address:", size_hint=(1, 0.4), font_size=sp(16))
        )
        self.to_address = TextInput(
            hint_text="LUN_...", multiline=False, size_hint=(1, 0.6), font_size=sp(16)
        )
        to_layout.add_widget(self.to_address)

        # Amount
        amount_layout = BoxLayout(orientation="vertical", size_hint=(1, 0.2))
        amount_layout.add_widget(
            Label(text="Amount:", size_hint=(1, 0.4), font_size=sp(16))
        )
        self.amount_input = TextInput(
            hint_text="0.000000",
            multiline=False,
            size_hint=(1, 0.6),
            font_size=sp(16),
            input_type="number",
        )
        amount_layout.add_widget(self.amount_input)

        # Memo
        memo_layout = BoxLayout(orientation="vertical", size_hint=(1, 0.2))
        memo_layout.add_widget(
            Label(text="Memo (optional):", size_hint=(1, 0.4), font_size=sp(16))
        )
        self.memo_input = TextInput(
            hint_text="Message", multiline=False, size_hint=(1, 0.6), font_size=sp(16)
        )
        memo_layout.add_widget(self.memo_input)

        # Send Button
        send_btn = Button(text="Send Transaction", size_hint=(1, 0.2), font_size=sp(18))
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
        if self.app and self.app.wallet:
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

                success = self.app.wallet.send_transaction(to_address, amount, memo)
                if success:
                    self.show_popup("Success", f"Sent {amount} LKC to {to_address}")
                    self.to_address.text = ""
                    self.amount_input.text = ""
                    self.memo_input.text = ""
                    self.app.update_all_screens()
                else:
                    self.show_popup("Error", "Failed to send transaction")

            except ValueError:
                self.show_popup("Error", "Invalid amount")

    def show_popup(self, title, message):
        content = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10))
        content.add_widget(Label(text=message, font_size=sp(16)))
        btn = Button(text="OK", size_hint=(1, 0.3), font_size=sp(16))
        popup = Popup(
            title=title, content=content, size_hint=(0.8, 0.4), title_size=sp(18)
        )
        btn.bind(on_press=popup.dismiss)
        content.add_widget(btn)
        popup.open()

    def update_data(self):
        """Update screen with wallet data"""
        if self.app and self.app.wallet and self.app.wallet.is_unlocked:
            wallet_info = self.app.wallet.get_wallet_info()
            if wallet_info:
                self.address_label.text = f'Your Address: {wallet_info["address"]}'

                # Generate QR code
                if wallet_info["address"]:
                    self.generate_qr_code(wallet_info["address"])

    def generate_qr_code(self, address):
        """Generate QR code for address"""
        try:
            # Use the library's QR code generation
            qr_data = self.app.wallet.generate_qr_code(address)
            if qr_data:
                self.qr_image.texture = Image(qr_data).texture
            else:
                # Fallback QR generation
                qr = qrcode.QRCode(version=1, box_size=4, border=4)
                qr.add_data(address)
                qr.make(fit=True)

                img = qr.make_image(fill_color="black", back_color="white")
                bio = io.BytesIO()
                img.save(bio, format="PNG")
                bio.seek(0)
                self.qr_image.texture = Image(bio).texture
        except Exception as e:
            print(f"QR generation error: {e}")

    def update_theme(self):
        """Update colors for theme"""
        self.address_label.color = self.theme.TEXT_PRIMARY


# ... (Keep the HistoryScreen, BottomNav, MainScreen classes the same as in your original code)
# For brevity, I'm showing the key fixes. The remaining classes should work as-is.


class LunaWalletApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.wallet = None
        self.is_dark_theme = True
        self.syncing = False
        self.is_unlocked = False

    def _on_window_size(self, instance, value):
        """Handle window size changes safely"""
        # Force a redraw to prevent graphics stack issues
        Clock.schedule_once(lambda dt: None, 0.1)

    def build(self):
        # Allow orientation changes
        if platform != "android" and platform != "ios":
            Window.size = (400, 700)  # Reasonable default for desktop

        # Initialize wallet backend
        self.wallet = LunaWallet()

        # Set up callbacks
        self.wallet.on_balance_changed = self.on_balance_changed
        self.wallet.on_transaction_received = self.on_transaction_received
        self.wallet.on_sync_complete = self.on_sync_complete
        self.wallet.on_error = self.on_error

        # Create main screen manager
        self.screen_manager = ScreenManager()
        # FIX: Bind to window size to prevent graphics issues
        Window.bind(size=self._on_window_size)
        # Check if wallet exists to determine which screen to show
        wallet_exists = os.path.exists(
            os.path.join(self.wallet.data_dir, self.wallet.wallet_file)
        )

        if wallet_exists:
            # Show password screen for existing wallet
            self.password_screen = PasswordScreen(name="password")
            self.password_screen.app = self
            self.screen_manager.add_widget(self.password_screen)
            self.screen_manager.current = "password"
        else:
            # Show setup screen for new users
            self.setup_screen = SetupScreen(name="setup")
            self.setup_screen.app = self
            self.screen_manager.add_widget(self.setup_screen)
            self.screen_manager.current = "setup"

        # Create main screen
        self.main_screen = MainScreen(name="main")
        self.main_screen.app = self

        # Set app references for main screen components
        for screen in self.main_screen.screen_manager.screens:
            screen.app = self

        # Add main screen to manager
        self.screen_manager.add_widget(self.main_screen)

        return self.screen_manager

    # Wallet management methods
    def initialize_wallet(self, password):
        """Initialize a new wallet"""
        try:
            success = self.wallet.initialize_wallet(password, "Primary Wallet")
            if success:
                self.is_unlocked = True
                Clock.schedule_once(lambda dt: self.update_all_screens(), 0.1)
                return True
            return False
        except Exception as e:
            print(f"Initialization error: {e}")
            return False

    def restore_wallet(self, private_key, password):
        """Restore wallet from private key"""
        try:
            # First create wallet instance
            self.wallet = LunaWallet()
            # Set up callbacks again since we recreated the wallet
            self.wallet.on_balance_changed = self.on_balance_changed
            self.wallet.on_transaction_received = self.on_transaction_received
            self.wallet.on_sync_complete = self.on_sync_complete
            self.wallet.on_error = self.on_error

            # Import the wallet
            if self.wallet.import_wallet(private_key, "Restored Wallet"):
                # Save with password
                if self.wallet.save_wallet(password):
                    self.is_unlocked = True
                    Clock.schedule_once(lambda dt: self.update_all_screens(), 0.1)
                    return True
            return False
        except Exception as e:
            print(f"Restore error: {e}")
            return False

    def unlock_wallet(self, password):
        """Attempt to unlock wallet with password"""
        success = self.wallet.unlock_wallet(password)
        if success:
            self.is_unlocked = True
            Clock.schedule_once(lambda dt: self.update_all_screens(), 0.1)
            return True
        return False

    # Callback methods
    def on_balance_changed(self):
        """Called when balance changes"""
        Clock.schedule_once(lambda dt: self.update_all_screens(), 0)

    def on_transaction_received(self):
        """Called when new transaction is received"""
        Clock.schedule_once(lambda dt: self.update_all_screens(), 0)

    def on_sync_complete(self):
        """Called when sync completes"""
        Clock.schedule_once(lambda dt: self.sync_complete(), 0)

    def on_error(self, message):
        """Called when error occurs"""
        print(f"Wallet error: {message}")

    def toggle_theme(self):
        """Toggle between dark and light themes"""
        self.is_dark_theme = not self.is_dark_theme
        if self.is_dark_theme:
            self.apply_theme(DarkTheme())
        else:
            self.apply_theme(LightTheme())

    def apply_theme(self, theme):
        """Apply theme to all screens"""
        for screen in self.screen_manager.screens:
            if hasattr(screen, "apply_theme"):
                screen.apply_theme(theme)

    def sync_wallet(self):
        """Manual sync with blockchain"""
        if self.syncing or not self.is_unlocked:
            return

        self.syncing = True
        # Find balance screen and update indicator
        if hasattr(self, "main_screen"):
            balance_screen = self.main_screen.screen_manager.get_screen("balance")
            balance_screen.sync_indicator.text = "⏳"

        def sync_thread():
            try:
                self.wallet.scan_blockchain()
            except Exception as e:
                print(f"Sync error: {e}")
            finally:
                Clock.schedule_once(lambda dt: self.sync_complete(), 0)

        threading.Thread(target=sync_thread, daemon=True).start()

    def sync_complete(self):
        """Called when sync completes"""
        self.syncing = False
        # Find balance screen and update indicator
        if hasattr(self, "main_screen"):
            balance_screen = self.main_screen.screen_manager.get_screen("balance")
            balance_screen.sync_indicator.text = "🔄"
            self.update_all_screens()

    def update_all_screens(self):
        """Update all screens with current wallet data"""
        if not self.is_unlocked or not hasattr(self, "main_screen"):
            return

        for screen in self.main_screen.screen_manager.screens:
            if hasattr(screen, "update_data"):
                screen.update_data()


if __name__ == "__main__":
    LunaWalletApp().run()
