#!/usr/bin/env python3
"""
Luna Wallet - Enhanced Version
Masked passwords, transaction history, proper balance sync
"""

import os
import sys
import json
import time
import hashlib
import secrets
import qrcode
import datetime
import threading
import requests
from cryptography.fernet import Fernet
import base64
import getpass

# ROYGBIV Color Scheme
COLORS = {
    "R": "\033[91m", "O": "\033[93m", "Y": "\033[93m", "G": "\033[92m",
    "B": "\033[94m", "I": "\033[95m", "V": "\033[95m", "X": "\033[0m",
    "BOLD": "\033[1m",
}

def color_text(text, color_code):
    return f"{color_code}{text}{COLORS['X']}"

class SecureDataManager:
    @staticmethod
    def get_data_dir():
        if getattr(sys, "frozen", False):
            # Check if we can write to executable directory
            base_dir = os.path.dirname(sys.executable)
            data_dir = os.path.join(base_dir, "data")
            
            # Try to create data directory in executable location
            try:
                os.makedirs(data_dir, exist_ok=True)
                # Test write permissions
                test_file = os.path.join(data_dir, "write_test.tmp")
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
                return data_dir
            except (OSError, IOError, PermissionError):
                # If we can't write to Program Files, use ProgramData
                if os.name == 'nt':  # Windows
                    program_data = os.environ.get('PROGRAMDATA', 'C:\\ProgramData')
                    app_data_dir = os.path.join(program_data, "Luna Wallet")
                    data_dir = os.path.join(app_data_dir, "data")
                else:  # Linux/Mac
                    home_dir = os.path.expanduser("~")
                    data_dir = os.path.join(home_dir, ".luna_wallet")
                
                os.makedirs(data_dir, exist_ok=True)
                return data_dir
        else:
            # Development mode - use local directory
            base_dir = os.path.dirname(os.path.abspath(__file__))
            data_dir = os.path.join(base_dir, "data")
            os.makedirs(data_dir, exist_ok=True)
            return data_dir

    @staticmethod
    def generate_key_from_password(password):
        """Generate encryption key from password"""
        return base64.urlsafe_b64encode(hashlib.sha256(password.encode()).digest())

    @staticmethod
    def save_encrypted_wallet(filename, data, password):
        """Save wallet with encryption"""
        try:
            key = SecureDataManager.generate_key_from_password(password)
            fernet = Fernet(key)
            encrypted_data = fernet.encrypt(json.dumps(data).encode())
            
            filepath = os.path.join(SecureDataManager.get_data_dir(), filename)
            with open(filepath, 'wb') as f:
                f.write(encrypted_data)
            return True
        except Exception as e:
            print(color_text(f"❌ Encryption error: {e}", COLORS["R"]))
            return False

    @staticmethod
    def load_encrypted_wallet(filename, password):
        """Load encrypted wallet"""
        try:
            filepath = os.path.join(SecureDataManager.get_data_dir(), filename)
            if not os.path.exists(filepath):
                return None
                
            with open(filepath, 'rb') as f:
                encrypted_data = f.read()
            
            key = SecureDataManager.generate_key_from_password(password)
            fernet = Fernet(key)
            decrypted_data = fernet.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
        except Exception as e:
            print(color_text(f"❌ Decryption error: {e}", COLORS["R"]))
            return None

    @staticmethod
    def save_json(filename, data):
        """Save unencrypted JSON (for non-sensitive data)"""
        filepath = os.path.join(SecureDataManager.get_data_dir(), filename)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        return True

    @staticmethod
    def load_json(filename, default=None):
        """Load unencrypted JSON"""
        if default is None:
            default = []
        filepath = os.path.join(SecureDataManager.get_data_dir(), filename)
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
        return default

class LunaWallet:
    def __init__(self):
        self.wallet_file = "wallet_encrypted.dat"
        self.pending_file = "pending.json"
        self.data_dir = SecureDataManager.get_data_dir()
        
        
        # Load or create wallet
        self.wallets = self.load_wallet() or []
        self.pending_txs = SecureDataManager.load_json(self.pending_file, [])
        
        if not self.wallets:
            self.first_time_setup()
        self.password = None
        self.password_timestamp = 0
        self.PASSWORD_TIMEOUT = 300  # 5 minutes
        # Fix any existing wallets that might be missing the pending_send field
        for wallet in self.wallets:
            if "pending_send" not in wallet:
                wallet["pending_send"] = 0.0
        
        # Start auto-scan thread
        self.scanning = True
        self.scan_thread = threading.Thread(target=self.auto_scanner, daemon=True)
        self.scan_thread.start()
        
        print(color_text("🚀 Luna Wallet Started - Auto-scanning enabled", COLORS["G"]))

    def get_password(self, prompt="Enter password: ", confirm=False):
        """Get password with masking and optional confirmation"""
        while True:
            password = getpass.getpass(color_text(prompt, COLORS["B"]))
            if not password:
                print(color_text("❌ Password cannot be empty", COLORS["R"]))
                continue
                
            if confirm:
                confirm_pw = getpass.getpass(color_text("Confirm password: ", COLORS["B"]))
                if password != confirm_pw:
                    print(color_text("❌ Passwords don't match", COLORS["R"]))
                    continue
                    
            return password

    def confirm_action(self, message):
        """Confirm dangerous actions"""
        response = input(color_text(f"{message} (y/N): ", COLORS["R"])).strip().lower()
        return response in ['y', 'yes']

    def first_time_setup(self):
        """Create first wallet automatically with password setup"""
        print(color_text("\n🎉 First Time Setup", COLORS["BOLD"]))
        self.create_wallet("Primary Wallet")
        
        # Set encryption password with confirmation
        password = self.get_password("🔐 Set wallet encryption password: ", confirm=True)
        if self.save_wallet(password):
            print(color_text("✅ Wallet encrypted and saved", COLORS["G"]))
        else:
            print(color_text("❌ Failed to save wallet", COLORS["R"]))

    def load_wallet(self):
        """Load encrypted wallet on startup"""
        if not os.path.exists(os.path.join(self.data_dir, self.wallet_file)):
            return None
            
        password = self.get_password("🔐 Enter wallet password: ")
        wallets = SecureDataManager.load_encrypted_wallet(self.wallet_file, password)
        
        if wallets is None:
            print(color_text("❌ Wrong password or corrupted wallet", COLORS["R"]))
            sys.exit(1)
            
        # Store the password for background saves
        self.password = password
        self.password_timestamp = time.time()
        print(color_text(f"✅ Loaded {len(wallets)} wallets", COLORS["G"]))
        return wallets

    def get_cached_password(self):
        """Get cached password if still valid"""
        if (self.password and 
            time.time() - self.password_timestamp < self.PASSWORD_TIMEOUT):
            return self.password
        return None

    def save_wallet(self, password=None, background=False):
        """Save wallet with encryption"""
        if password is None:
            if background:
                # In background mode, use cached password or skip
                password = self.get_cached_password()
                if not password:
                    return False  # Skip save if no cached password
            else:
                # In foreground mode, prompt and cache
                password = self.get_password("🔐 Enter password to save: ")
                self.password = password
                self.password_timestamp = time.time()
        
        return SecureDataManager.save_encrypted_wallet(self.wallet_file, self.wallets, password)
        
        return SecureDataManager.save_encrypted_wallet(self.wallet_file, self.wallets, password)
    def fix_wallet_structure(self):
        """Fix wallet structure for existing wallets"""
        for wallet in self.wallets:
            if "pending_send" not in wallet:
                wallet["pending_send"] = 0.0
        self.save_wallet()
        print(color_text("✅ Wallet structure fixed", COLORS["G"]))
    def create_wallet(self, label):
        """Create a new wallet with proper keys"""
        private_key = secrets.token_hex(32)
        public_key = hashlib.sha256(private_key.encode()).hexdigest()
        
        # Generate LUN address format
        address = f"LUN_{public_key[:16]}_{secrets.token_hex(4)}"
        
        wallet = {
            "address": address,
            "label": label,
            "public_key": public_key,
            "private_key": private_key,
            "balance": 0.0,
            "pending_send": 0.0,  # Make sure this is always included
            "transactions": [],
            "created": time.time(),
            "is_our_wallet": True
        }
        
        self.wallets.append(wallet)
        print(color_text(f"✅ Created: {address}", COLORS["G"]))
        return address

    def auto_scanner(self):
        """Background thread to auto-scan for new transactions and rewards"""
        while self.scanning:
            try:
                
                self.scan_blockchain()
                if self.updates:
                    self.save_wallet(background=True)
                    print(color_text("📊 Blockchain scan completed - balances updated", COLORS["B"]))
                time.sleep(30)  # Scan every 30 seconds
            except Exception as e:
                print(color_text(f"Scan error: {e}", COLORS["R"]))
                time.sleep(60)
    def auto_scanner(self):
        """Background thread to auto-scan for new transactions and rewards"""
        while self.scanning:
            try:
                # Reset updates flag at start of scan
                self.updates = False
                
                self.scan_blockchain()
                
                # Only save if updates were found AND we have a cached password
                if self.updates:
                    if self.save_wallet(background=True):
                        print(color_text("📊 Blockchain scan completed - balances updated", COLORS["B"]))
                    else:
                        print(color_text("⚠️  Updates found but no cached password - run 'sync' to save", COLORS["Y"]))
                
                time.sleep(30)  # Scan every 30 seconds
            except Exception as e:
                print(color_text(f"Scan error: {e}", COLORS["R"]))
                time.sleep(60)
    def scan_blockchain(self):
        """Fast blockchain scan for our wallets only"""
        blockchain = self.get_blockchain()
        if not blockchain:
            return

        # Don't reset updates here - let auto_scanner handle that
        for wallet in self.wallets:
            # Only scan for wallets we control
            if not wallet.get("is_our_wallet", True):
                continue
                
            old_balance = wallet["balance"]
            old_tx_count = len(wallet["transactions"])
            
            self.scan_wallet_transactions(wallet, blockchain)
            
            if wallet["balance"] != old_balance or len(wallet["transactions"]) != old_tx_count:
                self.updates = True  # Set the flag when updates are found

        # Update pending transactions
        if self.update_pending_transactions(blockchain):
            self.updates = True

    def scan_wallet_transactions(self, wallet, blockchain):
        """Scan blockchain for transactions involving this wallet"""
        address = wallet["address"]
        known_tx_hashes = {tx.get("hash") for tx in wallet["transactions"]}
        new_balance = 0.0
        
        # Initialize pending_send if it doesn't exist
        if "pending_send" not in wallet:
            wallet["pending_send"] = 0.0
        
        for block in blockchain:
            # Check block reward
            miner = block.get("miner")
            reward = float(block.get("reward", 0))
            # Case-insensitive comparison for miner address
            if miner and address.lower() == miner.lower() and reward > 0:
                reward_tx = {
                    "type": "reward",
                    "from": "network",
                    "to": address,
                    "amount": reward,
                    "timestamp": block.get("timestamp", time.time()),
                    "block_height": block.get("index", 0),
                    "hash": f"reward_{block.get('index', 0)}_{miner}",
                    "status": "confirmed"
                }
                if reward_tx["hash"] not in known_tx_hashes:
                    wallet["transactions"].append(reward_tx)
                    known_tx_hashes.add(reward_tx["hash"])
                    print(color_text(f"💰 Reward found: {reward} LKC", COLORS["G"]))

            # Check regular transactions
            for tx in block.get("transactions", []):
                tx_hash = tx.get("hash")
                if not tx_hash or tx_hash in known_tx_hashes:
                    continue
                    
                # Check if this transaction involves our wallet (case-insensitive)
                from_addr = tx.get("from") or tx.get("sender")
                to_addr = tx.get("to") or tx.get("receiver")
                
                # Case-insensitive address comparison
                if (from_addr and from_addr.lower() == address.lower()) or (to_addr and to_addr.lower() == address.lower()):
                    # Add to transactions
                    tx["status"] = "confirmed"
                    tx["block_height"] = block.get("index", 0)
                    wallet["transactions"].append(tx)
                    known_tx_hashes.add(tx_hash)
                    
                    direction = "⬅️ IN" if to_addr and to_addr.lower() == address.lower() else "➡️ OUT"
                    print(color_text(f"📥 Transaction found: {tx.get('amount', 0)} LKC {direction}", COLORS["B"]))

        # Recalculate balance from all transactions
        wallet["balance"] = self.calculate_balance_from_transactions(wallet["transactions"], address)
        
        # Clear pending send if transactions are confirmed
        for tx in wallet["transactions"]:
            if (tx.get("from") and tx.get("from").lower() == address.lower() and 
                tx.get("status") == "confirmed" and
                tx.get("hash") in [ptx.get("hash") for ptx in self.pending_txs]):
                wallet["pending_send"] = max(0, wallet["pending_send"] - float(tx.get("amount", 0)))

    def calculate_balance_from_transactions(self, transactions, address):
        """Calculate balance from transaction history"""
        balance = 0.0
        for tx in transactions:
            if tx.get("status") != "confirmed":
                continue
                
            tx_type = tx.get("type")
            from_addr = tx.get("from")
            to_addr = tx.get("to")
            amount = float(tx.get("amount", 0))
            
            # Case-insensitive address comparison
            if tx_type == "reward" and to_addr and to_addr.lower() == address.lower():
                balance += amount
            elif from_addr and from_addr.lower() == address.lower():
                balance -= amount
            elif to_addr and to_addr.lower() == address.lower():
                balance += amount
                
        return balance

    def update_pending_transactions(self, blockchain):
        """Update status of pending transactions - return True if updates were made"""
        blockchain_hashes = set()
        updated = False
        
        # Get all transaction hashes from blockchain
        for block in blockchain:
            for tx in block.get("transactions", []):
                blockchain_hashes.add(tx.get("hash"))
        
        # Update pending transactions
        for pending_tx in self.pending_txs[:]:
            if pending_tx.get("hash") in blockchain_hashes:
                pending_tx["status"] = "confirmed"
                updated = True
                print(color_text(f"✅ Transaction confirmed: {pending_tx.get('hash', '')[:16]}...", COLORS["G"]))
            elif pending_tx.get("timestamp", 0) < time.time() - 3600:  # 1 hour timeout
                pending_tx["status"] = "failed"
                updated = True
                print(color_text(f"❌ Transaction failed: {pending_tx.get('hash', '')[:16]}...", COLORS["R"]))
                
                # Refund pending balance
                for wallet in self.wallets:
                    if wallet["address"] == pending_tx.get("from"):
                        wallet["pending_send"] = max(0, wallet["pending_send"] - float(pending_tx.get("amount", 0)))
        
        if updated:
            SecureDataManager.save_json(self.pending_file, self.pending_txs)
        
        return updated

    def get_blockchain(self):
        """Get blockchain data"""
        try:
            response = requests.get("https://bank.linglin.art/blockchain", timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(color_text(f"❌ Blockchain error: {e}", COLORS["R"]))
        return []

    def send(self, to_address, amount, memo=""):
        """Send transaction with password confirmation"""
        if not self.wallets:
            print(color_text("❌ No wallets", COLORS["R"]))
            return False

        # Use first wallet
        wallet = self.wallets[0]
        available_balance = wallet["balance"] - wallet["pending_send"]
        
        if available_balance < amount:
            print(color_text(f"❌ Insufficient balance. Available: {available_balance} LKC", COLORS["R"]))
            return False

        # Confirm with password
        if not self.confirm_action(f"Send {amount} LKC to {to_address}?"):
            print(color_text("❌ Transaction cancelled", COLORS["R"]))
            return False
            
        password = self.get_password("🔐 Confirm transaction with password: ")
        if not self.verify_password(password):
            print(color_text("❌ Wrong password", COLORS["R"]))
            return False

        # Create transaction
        tx = {
            "type": "transfer",
            "from": wallet["address"],
            "to": to_address,
            "amount": float(amount),
            "fee": 0.00001,
            "nonce": int(time.time() * 1000),
            "timestamp": time.time(),
            "memo": memo,
        }
        
        # Sign transaction
        tx_data = f"{tx['from']}{tx['to']}{tx['amount']}{tx['timestamp']}{tx['nonce']}"
        tx["signature"] = hashlib.sha256(tx_data.encode()).hexdigest()
        tx["hash"] = hashlib.sha256(json.dumps(tx, sort_keys=True).encode()).hexdigest()

        # Broadcast to mempool
        try:
            response = requests.post("https://bank.linglin.art/mempool/add", json=tx, timeout=10)
            if response.status_code == 201:
                print(color_text(f"✅ Sent {amount} LKC to {to_address}", COLORS["G"]))
                
                # Add to pending and update pending balance
                self.pending_txs.append({
                    "hash": tx["hash"],
                    "from": wallet["address"],
                    "to": to_address,
                    "amount": amount,
                    "status": "pending",
                    "timestamp": time.time()
                })
                SecureDataManager.save_json(self.pending_file, self.pending_txs)
                
                wallet["pending_send"] += amount
                self.save_wallet()
                
                return True
        except Exception as e:
            print(color_text(f"❌ Send failed: {e}", COLORS["R"]))
        
        return False

    def verify_password(self, password):
        """Verify password is correct"""
        try:
            test_data = {"test": "data"}
            encrypted = SecureDataManager.save_encrypted_wallet("test.tmp", test_data, password)
            if encrypted:
                os.remove(os.path.join(self.data_dir, "test.tmp"))
                return True
        except:
            pass
        return False

    def receive(self):
        """Show receive address"""
        if not self.wallets:
            return False
            
        wallet = self.wallets[0]
        print(color_text(f"\n📥 Receive Address: {wallet['address']}", COLORS["G"]))
        print(color_text(f"🏷️  Label: {wallet['label']}", COLORS["B"]))
        
        # Generate QR code
        qr = qrcode.QRCode()
        qr.add_data(wallet['address'])
        qr.print_ascii()
        
        return True

    def import_wallet(self, private_key_hex, label=""):
        """Import wallet from private key"""
        try:
            # Validate private key
            if len(private_key_hex) != 64 or not all(c in '0123456789abcdef' for c in private_key_hex.lower()):
                print(color_text("❌ Invalid private key format", COLORS["R"]))
                return False

            # Generate public key and address
            public_key = hashlib.sha256(private_key_hex.encode()).hexdigest()
            address = f"LUN_{public_key[:16]}_{secrets.token_hex(4)}"
            
            # Check if already exists
            for wallet in self.wallets:
                if wallet["address"] == address:
                    print(color_text("❌ Wallet already exists", COLORS["R"]))
                    return False

            # Create wallet
            wallet = {
                "address": address,
                "label": label or f"Imported_{address[-8:]}",
                "public_key": public_key,
                "private_key": private_key_hex,
                "balance": 0.0,
                "pending_send": 0.0,
                "transactions": [],
                "created": time.time(),
                "is_our_wallet": True
            }
            
            self.wallets.append(wallet)
            self.save_wallet()
            
            # Scan for existing transactions
            print(color_text("🔍 Scanning for existing transactions...", COLORS["B"]))
            self.scan_blockchain()
            
            print(color_text(f"✅ Imported: {address}", COLORS["G"]))
            return True
            
        except Exception as e:
            print(color_text(f"❌ Import failed: {e}", COLORS["R"]))
            return False

    def export_wallet(self, address=None):
        """Export wallet private key with password confirmation"""
        if not self.wallets:
            return False
            
        wallet = self.wallets[0] if address is None else \
                next((w for w in self.wallets if w["address"] == address), None)
        
        if not wallet:
            print(color_text("❌ Wallet not found", COLORS["R"]))
            return False

        # Confirm export
        if not self.confirm_action("EXPORT PRIVATE KEY - THIS IS DANGEROUS"):
            print(color_text("❌ Export cancelled", COLORS["R"]))
            return False
            
        password = self.get_password("🔐 Confirm export with password: ")
        if not self.verify_password(password):
            print(color_text("❌ Wrong password", COLORS["R"]))
            return False

        print(color_text(f"\n🔐 PRIVATE KEY EXPORT", COLORS["R"]))
        print(color_text("=" * 50, COLORS["R"]))
        print(color_text(f"Address: {wallet['address']}", COLORS["B"]))
        print(color_text(f"Private Key: {wallet['private_key']}", COLORS["R"]))
        print(color_text("=" * 50, COLORS["R"]))
        print(color_text("⚠️  KEEP THIS SECURE! NEVER SHARE!", COLORS["R"]))
        
        return True

    def show_transaction_history(self):
        """Show detailed transaction history"""
        if not self.wallets:
            print(color_text("❌ No wallets", COLORS["R"]))
            return

        print(color_text("\n📊 Transaction History", COLORS["BOLD"]))
        print("=" * 60)
        
        all_transactions = []
        for wallet in self.wallets:
            for tx in wallet["transactions"]:
                tx["wallet_address"] = wallet["address"]
                tx["wallet_label"] = wallet["label"]
                all_transactions.append(tx)
        
        # Add pending transactions
        for pending_tx in self.pending_txs:
            if pending_tx.get("status") == "pending":
                pending_tx["wallet_address"] = pending_tx.get("from")
                pending_tx["wallet_label"] = "Pending"
                all_transactions.append(pending_tx)

        # Sort by timestamp (newest first)
        all_transactions.sort(key=lambda x: x.get("timestamp", 0), reverse=True)

        if not all_transactions:
            print(color_text("No transactions found", COLORS["O"]))
            return

        for i, tx in enumerate(all_transactions, 1):
            status = tx.get("status", "unknown")
            tx_type = tx.get("type", "transfer")
            
            # Status and type icons
            if status == "confirmed":
                status_icon = "✅"
                status_color = COLORS["G"]
            elif status == "pending":
                status_icon = "⏳"
                status_color = COLORS["Y"]
            elif status == "failed":
                status_icon = "❌"
                status_color = COLORS["R"]
            else:
                status_icon = "❓"
                status_color = COLORS["R"]

            if tx_type == "reward":
                type_icon = "💰"
            else:
                from_addr = tx.get("from", "")
                to_addr = tx.get("to", "")
                wallet_addr = tx.get("wallet_address", "")
                
                if from_addr == wallet_addr:
                    type_icon = "➡️"
                else:
                    type_icon = "⬅️"

            amount = tx.get("amount", 0)
            memo = tx.get("memo", "")
            
            print(f"{i}. {status_color}{status_icon} {type_icon} {amount:.6f} LKC{COLORS['X']}")
            print(f"   From: {tx.get('from', 'Network')}")
            print(f"   To: {tx.get('to', 'Unknown')}")
            print(f"   Status: {status_color}{status}{COLORS['X']}")
            
            if memo:
                print(f"   Memo: {memo}")
                
            print(f"   Time: {datetime.datetime.fromtimestamp(tx.get('timestamp', 0))}")
            print(f"   Hash: {tx.get('hash', 'N/A')[:20]}...")
            print()

    def status(self):
        """Show wallet status"""
        print(color_text("\n📊 Wallet Status", COLORS["BOLD"]))
        print("=" * 50)
        
        for wallet in self.wallets:
            available_balance = wallet["balance"] - wallet["pending_send"]
            
            print(color_text(f"\n🏷️  {wallet['label']}", COLORS["B"]))
            print(f"   Address: {wallet['address']}")
            print(f"   Balance: {wallet['balance']:.6f} LKC")
            print(f"   Available: {available_balance:.6f} LKC")
            print(f"   Pending: {wallet['pending_send']:.6f} LKC")
            print(f"   Transactions: {len(wallet['transactions'])}")

    def sync(self):
        """Manual sync"""
        print(color_text("🔄 Syncing with blockchain...", COLORS["B"]))
        self.scan_blockchain()
        print(color_text("✅ Sync complete", COLORS["G"]))

def main():
    wallet = LunaWallet()
    
    print(color_text("\n💡 Commands: status, send, receive, history, sync, import, export, new, exit", COLORS["I"]))
    
    while True:
        try:
            cmd = input(color_text("\n💰 wallet> ", COLORS["BOLD"])).strip().lower()
            
            if cmd == "status":
                wallet.status()
            elif cmd == "sync":
                wallet.sync()
            elif cmd == "receive":
                wallet.receive()
            elif cmd == "history":
                wallet.show_transaction_history()
            elif cmd.startswith("send"):
                parts = cmd.split()
                if len(parts) >= 3:
                    wallet.send(parts[1], float(parts[2]), " ".join(parts[3:]) if len(parts) > 3 else "")
                else:
                    print("Usage: send <address> <amount> [memo]")
            elif cmd == "new":
                label = input("Wallet label: ").strip() or "New Wallet"
                wallet.create_wallet(label)
                wallet.save_wallet()
            elif cmd == "import":
                private_key = input("Private key: ").strip()
                label = input("Label (optional): ").strip()
                wallet.import_wallet(private_key, label)
            elif cmd == "export":
                wallet.export_wallet()
            # Add this temporary command to your main loop:
            elif cmd == "fix":
                for wallet in wallet.wallets:
                    if "pending_send" not in wallet:
                        wallet["pending_send"] = 0.0
                wallet.save_wallet()
                print("✅ Fixed wallet structure")
            elif cmd in ["exit", "quit"]:
                wallet.scanning = False
                wallet.save_wallet()
                print(color_text("👋 Goodbye!", COLORS["G"]))
                break
            else:
                print(color_text("❌ Unknown command", COLORS["R"]))
                
        except KeyboardInterrupt:
            wallet.scanning = False
            wallet.save_wallet()
            print(color_text("\n👋 Goodbye!", COLORS["G"]))
            break
        except Exception as e:
            print(color_text(f"❌ Error: {e}", COLORS["R"]))

if __name__ == "__main__":
    main()