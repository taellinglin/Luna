#!/usr/bin/env python3
"""
Luna Wallet - Library Module
Enhanced version with proper encryption, transaction handling, and balance management
"""
import sys  # Add this
import io   # Add this
import os
import json
import time
import hashlib
import secrets
import threading
import requests
from cryptography.fernet import Fernet
import base64
import datetime

class SecureDataManager:
    """Handles encrypted storage and data management"""
    
    @staticmethod
    def get_data_dir():
        """Get application data directory"""
        if getattr(sys, "frozen", False):
            base_dir = os.path.dirname(sys.executable)
        else:
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
            print(f"Encryption error: {e}")
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
            print(f"Decryption error: {e}")
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
    """
    Main Luna Wallet library class
    Provides wallet functionality for GUI applications
    """
    
    # Also fix the __init__ method to initialize scan_thread:
    def __init__(self, auto_scan=True):
        self.wallet_file = "wallet_encrypted.dat"
        self.pending_file = "pending.json"
        self.data_dir = SecureDataManager.get_data_dir()
        
        # Initialize empty state - will be loaded by GUI
        self.wallets = []
        self.pending_txs = []
        self.is_unlocked = False
        self.scanning = False
        self.scan_thread = None  # Add this line
        
        # Event callbacks for GUI
        self.on_balance_changed = None
        self.on_transaction_received = None
        self.on_sync_complete = None
        self.on_error = None
        
        if auto_scan:
            self.start_auto_scan()

    # Core Wallet Operations
    def initialize_wallet(self, password, label="Primary Wallet"):
        """Initialize a new wallet with password protection"""
        try:
            # Create first wallet
            self.create_wallet(label)
            
            # Save with encryption
            if self.save_wallet(password):
                self.is_unlocked = True
                return True
            return False
        except Exception as e:
            self._handle_error(f"Initialization failed: {e}")
            return False

    def unlock_wallet(self, password):
        """Unlock wallet with password"""
        try:
            wallets = SecureDataManager.load_encrypted_wallet(self.wallet_file, password)
            if wallets is not None:
                self.wallets = wallets
                self.pending_txs = SecureDataManager.load_json(self.pending_file, [])
                self.is_unlocked = True
                
                # Ensure proper wallet structure
                for wallet in self.wallets:
                    if "pending_send" not in wallet:
                        wallet["pending_send"] = 0.0
                
                self._trigger_callback(self.on_balance_changed)
                return True
            return False
        except Exception as e:
            self._handle_error(f"Unlock failed: {e}")
            return False

    def lock_wallet(self):
        """Lock the wallet"""
        self.is_unlocked = False
        self.wallets = []
        self.pending_txs = []

    def save_wallet(self, password=None):
        """Save wallet with encryption"""
        if not self.is_unlocked:
            return False
            
        if password is None and not self.wallets:
            return False
            
        try:
            success = SecureDataManager.save_encrypted_wallet(
                self.wallet_file, self.wallets, password
            )
            if success:
                SecureDataManager.save_json(self.pending_file, self.pending_txs)
            return success
        except Exception as e:
            self._handle_error(f"Save failed: {e}")
            return False

    # Wallet Management
    def create_wallet(self, label):
        """Create a new wallet"""
        private_key = secrets.token_hex(32)
        public_key = hashlib.sha256(private_key.encode()).hexdigest()
        address = f"LUN_{public_key[:16]}_{secrets.token_hex(4)}"
        
        wallet = {
            "address": address,
            "label": label,
            "public_key": public_key,
            "private_key": private_key,
            "balance": 0.0,
            "pending_send": 0.0,
            "transactions": [],
            "created": time.time(),
            "is_our_wallet": True
        }
        
        self.wallets.append(wallet)
        return address

    def import_wallet(self, private_key_hex, label=""):
        """Import wallet from private key"""
        if not self.is_unlocked:
            return False
            
        try:
            if len(private_key_hex) != 64 or not all(c in '0123456789abcdef' for c in private_key_hex.lower()):
                return False

            public_key = hashlib.sha256(private_key_hex.encode()).hexdigest()
            address = f"LUN_{public_key[:16]}_{secrets.token_hex(4)}"
            
            # Check for duplicates
            for wallet in self.wallets:
                if wallet["address"] == address:
                    return False

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
            self.scan_blockchain()
            return True
            
        except Exception as e:
            self._handle_error(f"Import failed: {e}")
            return False

    def export_wallet(self, address=None):
        """Export wallet private key (use with caution)"""
        if not self.is_unlocked or not self.wallets:
            return None
            
        wallet = (self.wallets[0] if address is None else 
                 next((w for w in self.wallets if w["address"] == address), None))
        
        if wallet:
            return {
                "address": wallet["address"],
                "private_key": wallet["private_key"],
                "label": wallet["label"]
            }
        return None

    # Transaction Operations
    def send_transaction(self, to_address, amount, memo="", password=None):
        """Send transaction to address"""
        if not self.is_unlocked or not self.wallets:
            return False

        wallet = self.wallets[0]
        available_balance = wallet["balance"] - wallet["pending_send"]
        
        if available_balance < amount:
            self._handle_error(f"Insufficient balance. Available: {available_balance} LKC")
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
                # Add to pending
                self.pending_txs.append({
                    "hash": tx["hash"],
                    "from": wallet["address"],
                    "to": to_address,
                    "amount": amount,
                    "status": "pending",
                    "timestamp": time.time()
                })
                
                wallet["pending_send"] += amount
                self.save_wallet()
                self._trigger_callback(self.on_balance_changed)
                return True
        except Exception as e:
            self._handle_error(f"Send failed: {e}")
        
        return False

    # Blockchain Operations
    def scan_blockchain(self):
        """Manual blockchain scan"""
        if not self.is_unlocked:
            return False
            
        blockchain = self._get_blockchain()
        if not blockchain:
            return False

        updates = False
        for wallet in self.wallets:
            if not wallet.get("is_our_wallet", True):
                continue
                
            old_balance = wallet["balance"]
            old_tx_count = len(wallet["transactions"])
            
            self._scan_wallet_transactions(wallet, blockchain)
            
            if wallet["balance"] != old_balance or len(wallet["transactions"]) != old_tx_count:
                updates = True
                self._trigger_callback(self.on_transaction_received)

        self._update_pending_transactions(blockchain)

        if updates:
            self.save_wallet()
            self._trigger_callback(self.on_balance_changed)
        
        self._trigger_callback(self.on_sync_complete)
        return True

    def _scan_wallet_transactions(self, wallet, blockchain):
        """Scan blockchain for wallet transactions"""
        address = wallet["address"]
        known_tx_hashes = {tx.get("hash") for tx in wallet["transactions"]}
        
        for block in blockchain:
            # Check block reward
            miner = block.get("miner")
            reward = float(block.get("reward", 0))
            if miner == address and reward > 0:
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

            # Check regular transactions
            for tx in block.get("transactions", []):
                tx_hash = tx.get("hash")
                if not tx_hash or tx_hash in known_tx_hashes:
                    continue
                    
                from_addr = tx.get("from") or tx.get("sender")
                to_addr = tx.get("to") or tx.get("receiver")
                
                if from_addr == address or to_addr == address:
                    tx["status"] = "confirmed"
                    tx["block_height"] = block.get("index", 0)
                    wallet["transactions"].append(tx)
                    known_tx_hashes.add(tx_hash)

        # Recalculate balance
        wallet["balance"] = self._calculate_balance_from_transactions(wallet["transactions"], address)
        
        # Clear confirmed pending transactions
        for tx in wallet["transactions"]:
            if (tx.get("from") == address and 
                tx.get("status") == "confirmed" and
                tx.get("hash") in [ptx.get("hash") for ptx in self.pending_txs]):
                wallet["pending_send"] = max(0, wallet["pending_send"] - float(tx.get("amount", 0)))

    def _calculate_balance_from_transactions(self, transactions, address):
        """Calculate balance from transaction history"""
        balance = 0.0
        for tx in transactions:
            if tx.get("status") != "confirmed":
                continue
                
            tx_type = tx.get("type")
            from_addr = tx.get("from")
            to_addr = tx.get("to")
            amount = float(tx.get("amount", 0))
            
            if tx_type == "reward" and to_addr == address:
                balance += amount
            elif from_addr == address:
                balance -= amount
            elif to_addr == address:
                balance += amount
                
        return balance

    def _update_pending_transactions(self, blockchain):
        """Update pending transactions status"""
        blockchain_hashes = set()
        
        for block in blockchain:
            for tx in block.get("transactions", []):
                blockchain_hashes.add(tx.get("hash"))
        
        updated = False
        for pending_tx in self.pending_txs[:]:
            if pending_tx.get("hash") in blockchain_hashes:
                pending_tx["status"] = "confirmed"
                updated = True
            elif pending_tx.get("timestamp", 0) < time.time() - 3600:
                pending_tx["status"] = "failed"
                updated = True
                
                # Refund pending balance
                for wallet in self.wallets:
                    if wallet["address"] == pending_tx.get("from"):
                        wallet["pending_send"] = max(0, wallet["pending_send"] - float(pending_tx.get("amount", 0)))
        
        if updated:
            SecureDataManager.save_json(self.pending_file, self.pending_txs)
            self._trigger_callback(self.on_balance_changed)

    def _get_blockchain(self):
        """Get blockchain data from network"""
        try:
            response = requests.get("https://bank.linglin.art/blockchain", timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            self._handle_error(f"Blockchain error: {e}")
        return []

   
    # Auto-scan functionality
    def start_auto_scan(self):
        """Start background auto-scanning"""
        if hasattr(self, 'scanning') and self.scanning:
            return
            
        self.scanning = True
        self.scan_thread = threading.Thread(target=self._auto_scanner, daemon=True)
        self.scan_thread.start()

    def stop_auto_scan(self):
        """Stop background scanning"""
        if hasattr(self, 'scanning'):
            self.scanning = False
        if hasattr(self, 'scan_thread') and self.scan_thread:
            self.scan_thread.join(timeout=1)

    def _auto_scanner(self):
        """Background auto-scanner"""
        while hasattr(self, 'scanning') and self.scanning:
            try:
                if self.is_unlocked:
                    self.scan_blockchain()
                time.sleep(30)
            except Exception as e:
                self._handle_error(f"Auto-scan error: {e}")
                time.sleep(60)

    # Data Access Methods for GUI
    def get_wallet_info(self):
        """Get wallet information for GUI"""
        if not self.is_unlocked or not self.wallets:
            return None
            
        wallet = self.wallets[0]
        return {
            "address": wallet["address"],
            "label": wallet["label"],
            "balance": wallet["balance"],
            "available_balance": wallet["balance"] - wallet["pending_send"],
            "pending_send": wallet["pending_send"],
            "transaction_count": len(wallet["transactions"])
        }

    def get_transaction_history(self):
        """Get complete transaction history for GUI"""
        if not self.is_unlocked:
            return []
            
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
        return all_transactions

    def generate_qr_code(self, address):
        """Generate QR code data for address"""
        try:
            qr = qrcode.QRCode(version=1, box_size=4, border=4)
            qr.add_data(address)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            bio = io.BytesIO()
            img.save(bio, format='PNG')
            bio.seek(0)
            return bio
        except Exception as e:
            self._handle_error(f"QR generation error: {e}")
            return None

    # Callback Management
    def _trigger_callback(self, callback, *args):
        """Safely trigger callback if set"""
        if callback:
            try:
                callback(*args)
            except Exception as e:
                print(f"Callback error: {e}")

    def _handle_error(self, message):
        """Handle and report errors"""
        print(f"Wallet Error: {message}")
        self._trigger_callback(self.on_error, message)

    # Cleanup
    def __del__(self):
        """Cleanup on destruction"""
        self.stop_auto_scan()
        if hasattr(self, 'is_unlocked') and self.is_unlocked:
            self.save_wallet()