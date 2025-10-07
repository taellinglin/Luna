# Controller/balance_screen.py
from luna_wallet_lib import LunaWallet

class BalanceScreenController:
    def __init__(self, model):
        self.model = model
        self.wallet = LunaWallet()

    def get_wallet_info(self):
        """Get wallet information"""
        if self.wallet.is_unlocked:
            info = self.wallet.get_wallet_info()
            if info:
                self.model.balance = info["balance"]
                self.model.address = info["address"]
                self.model.transaction_count = info["transaction_count"]
                return info
        return None

    def sync_wallet(self):
        """Sync wallet with blockchain"""
        if self.wallet.is_unlocked:
            return self.wallet.scan_blockchain()
        return False