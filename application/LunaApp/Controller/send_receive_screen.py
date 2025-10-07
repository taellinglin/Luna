# Controller/send_receive_screen.py
from luna_wallet_lib import LunaWallet

class SendReceiveScreenController:
    def __init__(self, model):
        self.model = model
        self.wallet = LunaWallet()

    def get_wallet_address(self):
        """Get current wallet address"""
        if self.wallet.is_unlocked:
            info = self.wallet.get_wallet_info()
            return info["address"] if info else None
        return None

    def generate_qr_code(self, address):
        """Generate QR code for address"""
        if self.wallet.is_unlocked:
            return self.wallet.generate_qr_code(address)
        return None

    def send_transaction(self, to_address, amount, memo=""):
        """Send transaction"""
        if self.wallet.is_unlocked:
            success = self.wallet.send_transaction(to_address, amount, memo)
            self.model.send_success = success
            return success
        return False