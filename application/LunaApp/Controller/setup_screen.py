# Controller/setup_screen.py
from luna_wallet_lib import LunaWallet
import os

class SetupScreenController:
    def __init__(self, model):
        self.model = model
        self.wallet = LunaWallet()

    def create_wallet(self, password, label="Primary Wallet"):
        """Create a new wallet"""
        try:
            success = self.wallet.initialize_wallet(password, label)
            self.model.wallet_created = success
            return success
        except Exception as e:
            print(f"Create wallet error: {e}")
            return False

    def restore_wallet(self, private_key, password, label="Restored Wallet"):
        """Restore wallet from private key"""
        try:
            if self.wallet.import_wallet(private_key, label):
                if self.wallet.save_wallet(password):
                    self.model.wallet_restored = True
                    return True
            return False
        except Exception as e:
            print(f"Restore wallet error: {e}")
            return False

    def wallet_exists(self):
        """Check if wallet file exists"""
        wallet_path = os.path.join(self.wallet.data_dir, self.wallet.wallet_file)
        return os.path.exists(wallet_path)