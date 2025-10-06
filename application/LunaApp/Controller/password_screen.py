# Controller/password_screen.py
from luna_wallet_lib import LunaWallet

class PasswordScreenController:
    def __init__(self, model):
        self.model = model
        self.wallet = LunaWallet()

    def unlock_wallet(self, password):
        """Attempt to unlock wallet"""
        success = self.wallet.unlock_wallet(password)
        if success:
            self.model.password_correct = True
            self.model.attempts = 0
        else:
            self.model.attempts += 1
        return success