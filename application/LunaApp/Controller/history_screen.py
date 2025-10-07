# Controller/history_screen.py
from luna_wallet_lib import LunaWallet

class HistoryScreenController:
    def __init__(self, model):
        self.model = model
        self.wallet = LunaWallet()

    def get_transaction_history(self):
        """Get transaction history"""
        if self.wallet.is_unlocked:
            self.model.transactions = self.wallet.get_transaction_history()
            return self.model.transactions
        return []

    def import_wallet(self, private_key, label=""):
        """Import wallet"""
        if self.wallet.is_unlocked:
            return self.wallet.import_wallet(private_key, label)
        return False

    def create_wallet(self, label):
        """Create new wallet"""
        if self.wallet.is_unlocked:
            return self.wallet.create_wallet(label)
        return None

    def export_wallet(self, address=None):
        """Export wallet"""
        if self.wallet.is_unlocked:
            return self.wallet.export_wallet(address)
        return None