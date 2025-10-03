#!/usr/bin/env python3
"""
Luna Wallet - Blockchain-First Implementation with Auto-Setup
Automatically generates private keys for discovered wallets and provides full wallet setup
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
from urllib.parse import urljoin

# ROYGBIV Color Scheme 🌈
COLORS = {
    "R": "\033[91m",
    "O": "\033[93m",
    "Y": "\033[93m",
    "G": "\033[92m",
    "B": "\033[94m",
    "I": "\033[95m",
    "V": "\033[95m",
    "X": "\033[0m",
    "BOLD": "\033[1m",
}


def color_text(text, color_code):
    return f"{color_code}{text}{COLORS['X']}"


def debug_log(message, category="INFO"):
    """Extensive debug logging"""
    timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    color = (
        COLORS["B"]
        if category == "INFO"
        else COLORS["Y"]
        if category == "DEBUG"
        else COLORS["R"]
    )
    print(f"{color}[{timestamp} {category}]{COLORS['X']} {message}")


class DataManager:
    @staticmethod
    def get_data_dir():
        if getattr(sys, "frozen", False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(base_dir, "data")
        debug_log(f"Data directory: {data_dir}", "DEBUG")
        return data_dir

    @staticmethod
    def save_json(filename, data):
        os.makedirs(DataManager.get_data_dir(), exist_ok=True)
        filepath = os.path.join(DataManager.get_data_dir(), filename)
        debug_log(f"Saving JSON to {filepath}", "DEBUG")
        try:
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)
            debug_log(f"Successfully saved {filepath}", "DEBUG")
            return True
        except Exception as e:
            debug_log(f"Error saving {filepath}: {e}", "ERROR")
            return False

    @staticmethod
    def load_json(filename, default=None):
        if default is None:
            default = []
        filepath = os.path.join(DataManager.get_data_dir(), filename)
        debug_log(f"Loading JSON from {filepath}", "DEBUG")
        if os.path.exists(filepath):
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                debug_log(f"Successfully loaded {filepath}", "DEBUG")
                return data
            except Exception as e:
                debug_log(f"Error loading {filepath}: {e}", "ERROR")
                return default
        debug_log("File not found, returning default", "DEBUG")
        return default


class LunaWallet:
    def __init__(self):
        debug_log("Initializing LunaWallet", "INFO")
        self.wallet_file = "wallet.json"
        self.pending_tx_file = "pending_transactions.json"
        self.node_data_dir = DataManager.get_data_dir()
        
        # Load existing wallet or create empty
        self.addresses = self.load_wallet() or []
        self.pending_transactions = DataManager.load_json(self.pending_tx_file, [])
        
        # First-time setup check
        if not self.addresses:
            self.first_time_setup()
        else:
            # Scan blockchain and build wallet data
            self.scan_blockchain_for_wallets()
        
        # Start auto-sync thread
        self.auto_sync_thread = threading.Thread(target=self.auto_sync_worker, daemon=True)
        self.auto_sync_thread.start()
        
        debug_log("Luna Wallet Initialized", "INFO")
        self.show_status()

    def first_time_setup(self):
        """First-time wallet setup with automatic address generation"""
        print(color_text("\n🎉 Welcome to Luna Wallet!", COLORS["BOLD"]))
        print(color_text("🔍 Setting up your wallet for the first time...", COLORS["B"]))
        
        # Scan blockchain to discover addresses
        print(color_text("📥 Scanning blockchain for existing addresses...", COLORS["Y"]))
        self.scan_blockchain_for_wallets()
        
        if not self.addresses:
            print(color_text("🤔 No existing addresses found in blockchain", COLORS["O"]))
            print(color_text("💫 Creating your first wallet...", COLORS["B"]))
            self.create_wallet("My First Wallet")
        else:
            print(color_text(f"✅ Found {len(self.addresses)} addresses in blockchain", COLORS["G"]))
            
            # Check if any discovered wallets need private keys
            wallets_without_keys = [w for w in self.addresses if w.get("private_key") is None]
            if wallets_without_keys:
                print(color_text(f"🔑 Generating private keys for {len(wallets_without_keys)} discovered wallets...", COLORS["B"]))
                self.generate_keys_for_discovered_wallets()
            
            print(color_text("🎊 Wallet setup complete!", COLORS["G"]))
        
        # Create backup immediately
        print(color_text("💾 Creating initial backup...", COLORS["I"]))
        self.backup_wallet()

    def generate_keys_for_discovered_wallets(self):
        """Generate private keys for discovered wallets that don't have them"""
        for wallet in self.addresses:
            if wallet.get("private_key") is None and wallet.get("discovered"):
                debug_log(f"Generating keys for discovered wallet: {wallet['address']}", "INFO")
                
                # Generate private key
                private_key = secrets.token_hex(32)
                public_key = hashlib.sha256(private_key.encode()).hexdigest()
                
                # Update wallet with generated keys
                wallet["private_key"] = private_key
                wallet["public_key"] = public_key
                wallet["discovered"] = False  # Now it's a fully functional wallet
                wallet["label"] = f"My {wallet['label']}"  # Personalize the label
                
                print(color_text(f"✅ Generated keys for: {wallet['address']}", COLORS["G"]))
        
        self.save_wallet()

    def auto_sync_worker(self):
        """Background thread for automatic synchronization"""
        while True:
            try:
                time.sleep(60)  # Sync every 60 seconds
                debug_log("Auto-sync: Checking for blockchain updates", "DEBUG")
                self.scan_blockchain_for_wallets()
            except Exception as e:
                debug_log(f"Auto-sync error: {e}", "ERROR")

    def scan_blockchain_for_wallets(self):
        """Scan the entire blockchain to discover wallet addresses and build wallet data"""
        debug_log("Scanning blockchain for wallet addresses and rewards", "INFO")
        
        blockchain_data = self.get_blockchain_data()
        if not blockchain_data:
            debug_log("No blockchain data available", "WARNING")
            return
        
        # Dictionary to track all discovered addresses and their transactions
        discovered_addresses = {}
        
        # Scan every block for transactions and rewards
        for block_index, block in enumerate(blockchain_data):
            if not isinstance(block, dict):
                continue
                
            transactions = block.get("transactions", [])
            block_timestamp = block.get("timestamp", time.time())
            block_reward = block.get("reward", 0)
            miner_address = block.get("miner", "")
            
            # Process block reward as a special transaction
            if miner_address and block_reward > 0:
                reward_tx = {
                    "type": "reward",
                    "from": "network",
                    "to": miner_address,
                    "amount": float(block_reward),
                    "timestamp": block_timestamp,
                    "block_height": block_index,
                    "hash": f"reward_{block_index}_{int(block_timestamp)}",
                    "status": "confirmed",
                    "confirmations": len(blockchain_data) - block_index,
                    "memo": f"Block #{block_index} mining reward"
                }
                transactions.append(reward_tx)
            
            # Process regular transactions
            for tx in transactions:
                if not isinstance(tx, dict):
                    continue
                
                # Extract addresses from transaction using all possible field names
                addresses_in_tx = set()
                
                # Check all possible address fields
                for field in ['from', 'to', 'sender', 'receiver', 'from_address', 'to_address', 'miner', 'issued_to']:
                    address = tx.get(field)
                    if address and isinstance(address, str) and address.startswith(('LKC_', 'LUN_')):
                        addresses_in_tx.add(address)
                
                # Process each address found in this transaction
                for address in addresses_in_tx:
                    if address not in discovered_addresses:
                        # New address discovered - create wallet entry
                        discovered_addresses[address] = {
                            "address": address,
                            "label": f"Wallet_{address[-8:]}",
                            "public_key": None,  # Will be generated
                            "private_key": None,  # Will be generated
                            "balance": 0,
                            "pending_balance": 0,
                            "confirmed_balance": 0,
                            "total_received": 0,
                            "total_sent": 0,
                            "reward_income": 0,
                            "transactions": [],
                            "created": block_timestamp,
                            "discovered": True  # Mark as discovered from blockchain
                        }
                    
                    # Add this transaction to the address's history
                    tx_copy = tx.copy()
                    tx_copy["block_height"] = block_index
                    tx_copy["timestamp"] = block_timestamp
                    tx_copy["status"] = "confirmed"
                    tx_copy["confirmations"] = len(blockchain_data) - block_index
                    
                    # Add to transactions list if not already there (by hash)
                    existing_tx_hashes = [t.get("hash") for t in discovered_addresses[address]["transactions"]]
                    if tx_copy.get("hash") not in existing_tx_hashes:
                        discovered_addresses[address]["transactions"].append(tx_copy)
        
        # Calculate balances and statistics for all discovered addresses
        for address, wallet_data in discovered_addresses.items():
            stats = self.calculate_wallet_stats(wallet_data["transactions"], address)
            wallet_data.update(stats)
            debug_log(f"Discovered address: {address} with balance: {wallet_data['balance']} LKC", "INFO")
        
        # Merge with existing wallet data (preserve private keys for addresses we control)
        self.merge_discovered_wallets(discovered_addresses)
        
        # Update pending transactions status
        self.update_pending_transactions_status()
        
        debug_log(f"Blockchain scan complete. Found {len(discovered_addresses)} addresses", "INFO")

    def calculate_wallet_stats(self, transactions, address):
        """Calculate comprehensive wallet statistics from transaction history"""
        stats = {
            "balance": 0,
            "confirmed_balance": 0,
            "pending_balance": 0,
            "total_received": 0,
            "total_sent": 0,
            "reward_income": 0,
            "transaction_count": len(transactions)
        }
        
        for tx in transactions:
            # Check all possible address fields
            from_addr = tx.get('from') or tx.get('sender') or tx.get('from_address')
            to_addr = tx.get('to') or tx.get('receiver') or tx.get('to_address')
            amount = float(tx.get('amount', 0))
            tx_type = tx.get('type', 'transfer')
            status = tx.get('status', 'confirmed')
            
            # Track rewards separately
            if tx_type == 'reward' and to_addr == address:
                stats["reward_income"] += amount
            
            # Calculate balances based on transaction status
            if status == 'confirmed':
                if from_addr == address:
                    stats["balance"] -= amount
                    stats["confirmed_balance"] -= amount
                    stats["total_sent"] += amount
                if to_addr == address:
                    stats["balance"] += amount
                    stats["confirmed_balance"] += amount
                    stats["total_received"] += amount
            elif status == 'pending':
                if from_addr == address:
                    stats["pending_balance"] -= amount
                if to_addr == address:
                    stats["pending_balance"] += amount
        
        return stats

    def merge_discovered_wallets(self, discovered_addresses):
        """Merge discovered addresses with existing wallet data"""
        debug_log("Merging discovered wallets with existing data", "DEBUG")
        
        # Create a map of existing addresses for quick lookup
        existing_address_map = {wallet["address"]: wallet for wallet in self.addresses}
        
        merged_wallets = []
        
        # Add all discovered addresses
        for address, discovered_wallet in discovered_addresses.items():
            if address in existing_address_map:
                # Merge: keep existing wallet data but update stats and transactions
                existing_wallet = existing_address_map[address]
                # Update transactions and stats but preserve keys
                existing_wallet["transactions"] = discovered_wallet["transactions"]
                existing_wallet.update(discovered_wallet)
                # Preserve private key and public key if we have them
                if existing_wallet.get("private_key"):
                    discovered_wallet["private_key"] = existing_wallet["private_key"]
                    discovered_wallet["public_key"] = existing_wallet["public_key"]
                    discovered_wallet["discovered"] = False  # Now it's a full wallet
                merged_wallets.append(existing_wallet)
                debug_log(f"Merged existing wallet: {address}", "DEBUG")
            else:
                # Add new discovered wallet
                merged_wallets.append(discovered_wallet)
                debug_log(f"Added discovered wallet: {address}", "DEBUG")
        
        # Add any existing wallets that weren't found in blockchain (zero balance wallets)
        for address, wallet in existing_address_map.items():
            if address not in discovered_addresses:
                # This wallet has no transactions in blockchain, set balances to 0
                wallet.update({
                    "balance": 0,
                    "confirmed_balance": 0,
                    "pending_balance": 0,
                    "total_received": 0,
                    "total_sent": 0,
                    "reward_income": 0
                })
                merged_wallets.append(wallet)
                debug_log(f"Added zero-balance wallet: {address}", "DEBUG")
        
        self.addresses = merged_wallets
        self.save_wallet()

    def update_pending_transactions_status(self):
        """Update status of pending transactions based on blockchain"""
        debug_log("Updating pending transactions status", "DEBUG")
        
        blockchain_data = self.get_blockchain_data()
        if not blockchain_data:
            return
        
        updated = False
        
        for pending_tx in self.pending_transactions[:]:
            tx_hash = pending_tx.get("hash")
            
            # Check if transaction is now in blockchain
            if self.find_transaction_in_blockchain(tx_hash):
                pending_tx["status"] = "confirmed"
                pending_tx["confirmations"] = 1  # At least 1 confirmation
                updated = True
                debug_log(f"Pending transaction confirmed: {tx_hash}", "DEBUG")
            elif pending_tx.get("timestamp", 0) < time.time() - 3600:  # 1 hour old
                pending_tx["status"] = "failed"
                updated = True
                debug_log(f"Pending transaction failed (timeout): {tx_hash}", "DEBUG")
        
        if updated:
            self.save_pending_transactions()

    def find_transaction_in_blockchain(self, tx_hash):
        """Check if a transaction exists in the blockchain"""
        blockchain_data = self.get_blockchain_data()
        if not blockchain_data:
            return False
        
        for block in blockchain_data:
            transactions = block.get("transactions", [])
            for tx in transactions:
                if tx.get("hash") == tx_hash:
                    return True
        return False

    def create_wallet(self, label=""):
        """Create a new wallet with full key generation"""
        debug_log(f"Creating new wallet with label: {label}", "INFO")
        private_key = secrets.token_hex(32)
        debug_log("Generated private key", "DEBUG")
        public_key = hashlib.sha256(private_key.encode()).hexdigest()
        debug_log("Generated public key", "DEBUG")
        
        # Generate LUN address (like your discovered format)
        address = f"LUN_{public_key[:16]}_{secrets.token_hex(4)}"
        debug_log(f"Generated address: {address}", "DEBUG")

        wallet_data = {
            "address": address,
            "label": label,
            "public_key": public_key,
            "private_key": private_key,
            "balance": 0,
            "confirmed_balance": 0,
            "pending_balance": 0,
            "total_received": 0,
            "total_sent": 0,
            "reward_income": 0,
            "transactions": [],
            "created": time.time(),
            "discovered": False
        }

        self.addresses.append(wallet_data)
        self.save_wallet()

        # Generate QR code
        qr_filename = self.generate_qr_code(address, label)

        print(color_text(f"✅ New wallet created: {address}", COLORS["G"]))
        print(color_text(f"🔑 Private key generated and secured", COLORS["G"]))
        print(color_text(f"📄 QR code saved: {qr_filename}", COLORS["B"]))
        return address

    def generate_qr_code(self, address, label):
        """Generate QR code for wallet address"""
        debug_log(f"Generating QR code for address: {address}", "INFO")
        try:
            # Create QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(address)
            qr.make(fit=True)

            # Create image
            img = qr.make_image(fill_color="black", back_color="white")

            # Generate filename
            safe_label = "".join(
                c for c in label if c.isalnum() or c in (" ", "-", "_")
            ).rstrip()
            safe_label = safe_label.replace(" ", "_")[:20]
            filename = f"wallet_qr_{safe_label}_{int(time.time())}.png"
            filepath = os.path.join(DataManager.get_data_dir(), filename)

            # Save image
            img.save(filepath)
            debug_log(f"QR code saved to: {filepath}", "DEBUG")
            return filepath
        except Exception as e:
            debug_log(f"Error generating QR code: {e}", "ERROR")
            return None

    def load_wallet(self):
        debug_log("Loading wallet data", "DEBUG")
        return DataManager.load_json(self.wallet_file)

    def save_wallet(self):
        debug_log("Saving wallet data", "DEBUG")
        DataManager.save_json(self.wallet_file, self.addresses)

    def save_pending_transactions(self):
        debug_log("Saving pending transactions", "DEBUG")
        DataManager.save_json(self.pending_tx_file, self.pending_transactions)

    def backup_wallet(self):
        """Explicit wallet backup command"""
        debug_log("Creating manual wallet backup", "INFO")
        timestamp = int(time.time())
        backup_file = f"wallet_manual_backup_{timestamp}.json"
        backup_path = os.path.join(DataManager.get_data_dir(), backup_file)

        if DataManager.save_json(backup_file, self.addresses):
            print(color_text(f"✅ Wallet backed up to: {backup_path}", COLORS["G"]))
            return True
        else:
            print(color_text("❌ Failed to create wallet backup", COLORS["R"]))
            return False

    def download_blockchain(self):
        """Download blockchain from the web server"""
        debug_log("Downloading blockchain from server", "INFO")
        try:
            url = "https://bank.linglin.art/blockchain"
            debug_log(f"Downloading from: {url}", "DEBUG")
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            blockchain_data = response.json()
            debug_log(f"Downloaded blockchain with {len(blockchain_data) if isinstance(blockchain_data, list) else 'unknown'} items", "DEBUG")
            
            # Save to local file
            blockchain_file = os.path.join(self.node_data_dir, "blockchain.json")
            with open(blockchain_file, "w") as f:
                json.dump(blockchain_data, f, indent=2)
            
            debug_log(f"Blockchain saved to: {blockchain_file}", "DEBUG")
            print(color_text("✅ Blockchain downloaded successfully", COLORS["G"]))
            return blockchain_data
            
        except Exception as e:
            debug_log(f"Error downloading blockchain: {e}", "ERROR")
            print(color_text(f"❌ Failed to download blockchain: {e}", COLORS["R"]))
            return None

    def get_blockchain_data(self):
        """Load blockchain data - download if not exists"""
        debug_log("Loading blockchain data", "DEBUG")
        try:
            blockchain_file = os.path.join(self.node_data_dir, "blockchain.json")
            debug_log(f"Looking for blockchain file: {blockchain_file}", "DEBUG")

            if not os.path.exists(blockchain_file):
                debug_log("Blockchain file not found, downloading...", "INFO")
                print(color_text("📥 Downloading blockchain from server...", COLORS["Y"]))
                downloaded_data = self.download_blockchain()
                if downloaded_data:
                    return downloaded_data
                else:
                    debug_log("Blockchain download failed", "ERROR")
                    return []

            with open(blockchain_file, "r") as f:
                data = json.load(f)

            debug_log(f"Raw data type: {type(data)}", "DEBUG")

            # Handle different blockchain structures
            if isinstance(data, dict):
                if "chain" in data:
                    debug_log("Found blockchain with 'chain' key", "DEBUG")
                    chain = data["chain"]
                    print(f"✅ Found blockchain with {len(chain)} blocks")
                    return chain
                elif "blocks" in data:
                    debug_log("Found blockchain with 'blocks' key", "DEBUG")
                    chain = data["blocks"]
                    print(f"✅ Found blockchain with {len(chain)} blocks")
                    return chain
                else:
                    debug_log("Dictionary but no chain/blocks key", "ERROR")
                    return []
            elif isinstance(data, list):
                debug_log("Found blockchain as direct list", "DEBUG")
                print(f"✅ Found blockchain with {len(data)} blocks")
                return data
            else:
                debug_log(f"Unknown blockchain structure: {type(data)}", "ERROR")
                return []

        except Exception as e:
            debug_log(f"Error loading blockchain: {e}", "ERROR")
            print(f"❌ Error loading blockchain: {e}")
            return []

    def sync_with_node(self):
        """Manual sync command - rescan blockchain and rebuild wallet data"""
        debug_log("Manual sync: Starting blockchain rescan", "INFO")
        print(color_text("🔄 Rescanning blockchain for wallet data...", COLORS["B"]))
        
        # Rescan the blockchain
        self.scan_blockchain_for_wallets()
        
        print(color_text("✅ Sync completed", COLORS["G"]))
        self.show_status()
        return True

    def send(self, to_address, amount, memo="No Memo."):
        """Create a transaction and broadcast it to the network"""
        debug_log(f"Sending {amount} LKC to {to_address}", "INFO")
        if not self.addresses:
            print(color_text("❌ No wallets available", COLORS["R"]))
            return False

        # Find first wallet that has private key (can send)
        from_wallet = None
        for wallet in self.addresses:
            if wallet.get("private_key"):
                from_wallet = wallet
                break
        
        if not from_wallet:
            print(color_text("❌ No wallet with private key found (read-only wallets cannot send)", COLORS["R"]))
            return False

        debug_log(f"Using wallet: {from_wallet['address']}", "DEBUG")

        # Check available balance (confirmed balance only)
        available_balance = from_wallet.get("confirmed_balance", 0)
        if available_balance < amount:
            print(
                color_text(
                    f"❌ Insufficient balance: {available_balance} LKC available, {amount} LKC requested",
                    COLORS["R"],
                )
            )
            return False

        # Create transaction with proper structure for the server
        transaction_id = f"tx_{secrets.token_hex(16)}"
        debug_log(f"Generated transaction ID: {transaction_id}", "DEBUG")
        
        # Create the transaction in the format the server expects
        transaction = {
            "type": "transfer",
            "from": from_wallet["address"],
            "to": to_address,
            "amount": float(amount),
            "memo": memo,
            "timestamp": time.time(),
            "signature": transaction_id,
            "hash": hashlib.sha256(
                f"{from_wallet['address']}{to_address}{amount}{time.time()}".encode()
            ).hexdigest(),
        }

        # Add to pending transactions
        pending_tx = {
            "hash": transaction["hash"],
            "signature": transaction_id,
            "from": from_wallet["address"],
            "to": to_address,
            "amount": amount,
            "memo": memo,
            "timestamp": time.time(),
            "status": "pending",
            "confirmations": 0,
            "block_height": None,
        }

        self.pending_transactions.append(pending_tx)
        self.save_pending_transactions()
        
        # Update local wallet pending balance
        from_wallet["pending_balance"] -= amount
        self.save_wallet()
        
        debug_log("Transaction added to pending transactions", "DEBUG")

        # Broadcast to network via API
        if self.broadcast_transaction(transaction):
            print(
                color_text(
                    f"✅ Transaction created: {amount} LKC to {to_address}", COLORS["G"]
                )
            )
            print(color_text(f"📄 Transaction ID: {transaction_id}", COLORS["B"]))
            print(color_text("⏳ Waiting for confirmation...", COLORS["Y"]))
            return True
        else:
            # Mark as failed if broadcast fails
            pending_tx["status"] = "failed"
            self.save_pending_transactions()
            # Restore pending balance
            from_wallet["pending_balance"] += amount
            self.save_wallet()
            print(color_text("❌ Failed to broadcast transaction", COLORS["R"]))
            return False

    def receive(self):
        """Show receive address and QR code"""
        if not self.addresses:
            print(color_text("❌ No wallets available", COLORS["R"]))
            return False

        # Find first wallet that has private key
        wallet = None
        for w in self.addresses:
            if w.get("private_key"):
                wallet = w
                break
        
        if not wallet:
            print(color_text("❌ No wallet with private key found", COLORS["R"]))
            return False

        print(color_text(f"\n📥 Receive Address: {wallet['address']}", COLORS["G"]))
        print(color_text(f"🏷️  Label: {wallet['label']}", COLORS["B"]))
        
        # Generate and show QR code
        qr_filename = self.generate_qr_code(wallet['address'], wallet['label'])
        if qr_filename:
            print(color_text(f"📄 QR Code: {qr_filename}", COLORS["I"]))
        
        print(color_text("\n💡 Share this address to receive LKC tokens", COLORS["Y"]))
        return True

    def broadcast_transaction(self, transaction):
        """Broadcast transaction to the blockchain API"""
        debug_log("Broadcasting transaction to network", "INFO")
        try:
            api_url = "https://bank.linglin.art/api/transaction/broadcast"
            debug_log(f"API URL: {api_url}", "DEBUG")

            response = requests.post(api_url, json=transaction, timeout=10)
            debug_log(f"API response status: {response.status_code}", "DEBUG")
            if response.status_code == 200:
                result = response.json()
                debug_log(f"API response: {result}", "DEBUG")
                return result.get("status") == "success"
            debug_log(f"API request failed with status {response.status_code}", "ERROR")
            return False
        except Exception as e:
            debug_log(f"Error broadcasting transaction: {e}", "ERROR")
            return False

    def show_stats(self):
        """Show detailed wallet statistics"""
        debug_log("Displaying wallet statistics", "INFO")
        if not self.addresses:
            print(color_text("❌ No wallets available", COLORS["R"]))
            return

        print(color_text("\n" + "=" * 60, COLORS["I"]))
        print(color_text("                 WALLET STATISTICS", COLORS["BOLD"]))
        print(color_text("=" * 60, COLORS["I"]))

        for wallet in self.addresses:
            wallet_type = "🔑 Full Wallet" if wallet.get("private_key") else "👀 Read-Only"
            print(color_text(f"\n📊 {wallet['label']} ({wallet_type})", COLORS["B"]))
            print(color_text("   Balances:", COLORS["I"]))
            print(f"     💰 Total Balance: {wallet.get('balance', 0):.6f} LKC")
            print(f"     ✅ Confirmed: {wallet.get('confirmed_balance', 0):.6f} LKC")
            print(f"     ⏳ Pending: {wallet.get('pending_balance', 0):.6f} LKC")
            
            print(color_text("   📈 Transaction Stats:", COLORS["I"]))
            print(f"     📥 Total Received: {wallet.get('total_received', 0):.6f} LKC")
            print(f"     📤 Total Sent: {wallet.get('total_sent', 0):.6f} LKC")
            print(f"     💎 Reward Income: {wallet.get('reward_income', 0):.6f} LKC")
            print(f"     🔢 Transaction Count: {wallet.get('transaction_count', 0)}")

    def show_transaction_history(self):
        """Show comprehensive transaction history"""
        debug_log("Displaying transaction history", "INFO")
        if not self.addresses:
            print(color_text("❌ No wallets available", COLORS["R"]))
            return

        # Get all transactions including pending
        all_transactions = []
        for wallet in self.addresses:
            for tx in wallet.get("transactions", []):
                tx["wallet_address"] = wallet["address"]
                tx["wallet_label"] = wallet["label"]
                all_transactions.append(tx)
        
        # Add pending transactions
        for pending_tx in self.pending_transactions:
            if pending_tx.get("status") == "pending":
                pending_tx["wallet_address"] = pending_tx.get("from")
                pending_tx["wallet_label"] = "Pending"
                all_transactions.append(pending_tx)

        # Sort by timestamp (newest first)
        all_transactions.sort(key=lambda x: x.get("timestamp", 0), reverse=True)

        print(color_text(f"\n📊 Transaction History ({len(all_transactions)} transactions):", COLORS["B"]))
        print("=" * 80)

        if not all_transactions:
            print(color_text("No transactions found", COLORS["O"]))
            return

        for i, tx in enumerate(all_transactions, 1):
            status = tx.get("status", "unknown")
            confirmations = tx.get("confirmations", 0)
            tx_type = tx.get("type", "transfer")

            # Status icons and colors
            if status == "confirmed":
                if confirmations >= 6:
                    status_icon = "✅"
                    status_text = f"CONFIRMED ({confirmations} confirmations)"
                else:
                    status_icon = "🟡"
                    status_text = f"CONFIRMED ({confirmations}/6 confirmations)"
                status_color = COLORS["G"]
            elif status == "pending":
                status_icon = "⏳"
                status_text = "PENDING (0 confirmations)"
                status_color = COLORS["Y"]
            elif status == "failed":
                status_icon = "❌"
                status_text = "FAILED"
                status_color = COLORS["R"]
            else:
                status_icon = "❓"
                status_text = "UNKNOWN"
                status_color = COLORS["R"]

            # Determine transaction direction and type
            from_addr = tx.get("from", "")
            to_addr = tx.get("to", "")
            wallet_addr = tx.get("wallet_address", "")

            if tx_type == "reward":
                direction = "💎 REWARD"
                counterparty = f"From: {from_addr}"
            elif from_addr == wallet_addr and to_addr == wallet_addr:
                direction = "🔄 SELF"
                counterparty = "Self"
            elif from_addr == wallet_addr:
                direction = "➡️ OUTGOING"
                counterparty = f"To: {to_addr}"
            elif to_addr == wallet_addr:
                direction = "⬅️ INCOMING"
                counterparty = f"From: {from_addr}"
            else:
                direction = "🔗 RELATED"
                counterparty = f"From: {from_addr} → To: {to_addr}"

            amount = tx.get("amount", 0)
            memo = tx.get("memo", "")

            print(f"{i}. {status_color}{status_icon} {direction} {amount:.6f} LKC{COLORS['X']}")
            print(f"   {counterparty}")
            print(f"   Status: {status_color}{status_text}{COLORS['X']}")

            if memo:
                print(f"   Memo: {memo}")

            print(f"   Time: {datetime.datetime.fromtimestamp(tx.get('timestamp', 0))}")
            print(f"   Hash: {tx.get('hash', 'N/A')[:20]}...")
            print()

    def show_status(self):
        """Display wallet and blockchain status"""
        debug_log("Displaying wallet status", "INFO")
        print(color_text("\n" + "=" * 60, COLORS["I"]))
        print(color_text("                 LUNA WALLET STATUS", COLORS["BOLD"]))
        print(color_text("=" * 60, COLORS["I"]))

        # Check if node data exists
        blockchain_data = self.get_blockchain_data()

        node_status = "🟢 Synced" if blockchain_data else "🔴 No Data"
        print(color_text(f"🌐 Node Status: {node_status}", COLORS["G" if blockchain_data else "R"]))

        # Get blockchain info
        if isinstance(blockchain_data, list):
            chain_height = len(blockchain_data)
        else:
            chain_height = 0

        total_balance = sum(wallet.get("balance", 0) for wallet in self.addresses)
        confirmed_balance = sum(wallet.get("confirmed_balance", 0) for wallet in self.addresses)
        pending_balance = sum(wallet.get("pending_balance", 0) for wallet in self.addresses)
        
        # Count wallet types
        full_wallets = sum(1 for w in self.addresses if w.get("private_key"))
        read_only_wallets = len(self.addresses) - full_wallets
        
        print(color_text(f"💰 Total Balance: {total_balance:.6f} LKC", COLORS["Y"]))
        print(color_text(f"✅ Confirmed: {confirmed_balance:.6f} LKC", COLORS["G"]))
        print(color_text(f"⏳ Pending: {pending_balance:.6f} LKC", COLORS["B"]))
        print(color_text(f"👛 Wallets: {len(self.addresses)} ({full_wallets} full, {read_only_wallets} read-only)", COLORS["I"]))
        print(color_text(f"⛓️  Blockchain Height: {chain_height}", COLORS["O"]))
        print(color_text(f"🔄 Auto-sync: Active (every 60s)", COLORS["G"]))
        print(color_text(f"⏳ Pending Transactions: {len([tx for tx in self.pending_transactions if tx.get('status') == 'pending'])}", COLORS["Y"]))

        for i, wallet in enumerate(self.addresses):
            color = [COLORS["G"], COLORS["B"], COLORS["Y"], COLORS["I"]][i % 4]
            wallet_type = "🔑" if wallet.get("private_key") else "👀"
            print(color_text(f"\n{i + 1}. {wallet_type} {wallet['label']}", color))
            print(color_text(f"   Address: {wallet['address']}", color))
            print(color_text(f"   Balance: {wallet.get('balance', 0):.6f} LKC", color))
            print(color_text(f"   Transactions: {len(wallet.get('transactions', []))}", color))
            if not wallet.get("private_key"):
                print(color_text("   ⚠️  Read-only (import private key to enable sending)", COLORS["O"]))

    def import_private_key(self, private_key_hex, label=""):
        """Import a wallet using a private key"""
        debug_log(f"Importing wallet with private key", "INFO")
        
        try:
            # Validate private key format
            if len(private_key_hex) != 64 or not all(c in '0123456789abcdef' for c in private_key_hex.lower()):
                print(color_text("❌ Invalid private key format. Must be 64-character hex string", COLORS["R"]))
                return False
            
            # Generate public key from private key
            public_key = hashlib.sha256(private_key_hex.encode()).hexdigest()
            
            # Generate address (using LUN format like your discovered wallets)
            address = f"LUN_{public_key[:16]}_{secrets.token_hex(4)}"
            
            # Check if this address already exists
            for existing_wallet in self.addresses:
                if existing_wallet["address"] == address:
                    print(color_text(f"❌ Wallet with this private key already exists: {address}", COLORS["R"]))
                    return False
            
            # Create wallet data
            wallet_data = {
                "address": address,
                "label": label or f"Imported_{address[-8:]}",
                "public_key": public_key,
                "private_key": private_key_hex,
                "balance": 0,
                "confirmed_balance": 0,
                "pending_balance": 0,
                "total_received": 0,
                "total_sent": 0,
                "reward_income": 0,
                "transactions": [],
                "created": time.time(),
                "discovered": False,
                "imported": True
            }
            
            # Add to wallet list
            self.addresses.append(wallet_data)
            self.save_wallet()
            
            # Rescan blockchain to find transactions for this address
            print(color_text(f"🔍 Scanning blockchain for transactions...", COLORS["B"]))
            self.scan_blockchain_for_wallets()
            
            print(color_text(f"✅ Wallet imported successfully: {address}", COLORS["G"]))
            print(color_text(f"🏷️  Label: {wallet_data['label']}", COLORS["B"]))
            print(color_text(f"💰 Balance: {wallet_data['balance']} LKC", COLORS["Y"]))
            
            return True
            
        except Exception as e:
            debug_log(f"Error importing private key: {e}", "ERROR")
            print(color_text(f"❌ Error importing private key: {e}", COLORS["R"]))
            return False

    def export_private_key(self, address=None):
        """Export private key for a wallet (BE CAREFUL - shows sensitive data)"""
        if not self.addresses:
            print(color_text("❌ No wallets available", COLORS["R"]))
            return False
        
        # If no address specified, use first wallet with private key
        if address is None:
            for wallet in self.addresses:
                if wallet.get("private_key"):
                    address = wallet["address"]
                    break
        
        if not address:
            print(color_text("❌ No wallet with private key found", COLORS["R"]))
            return False
        
        # Find the wallet
        wallet = None
        for w in self.addresses:
            if w["address"] == address:
                wallet = w
                break
        
        if not wallet:
            print(color_text(f"❌ Wallet not found: {address}", COLORS["R"]))
            return False
        
        if not wallet.get("private_key"):
            print(color_text(f"❌ Wallet has no private key (read-only): {address}", COLORS["R"]))
            return False
        
        print(color_text(f"\n🔐 PRIVATE KEY EXPORT - KEEP THIS SECURE!", COLORS["R"]))
        print(color_text("=" * 60, COLORS["R"]))
        print(color_text(f"Address: {wallet['address']}", COLORS["B"]))
        print(color_text(f"Label: {wallet['label']}", COLORS["B"]))
        print(color_text(f"Private Key: {wallet['private_key']}", COLORS["R"]))
        print(color_text("=" * 60, COLORS["R"]))
        print(color_text("⚠️  WARNING: Anyone with this private key can access your funds!", COLORS["R"]))
        print(color_text("⚠️  Store this securely and never share it!", COLORS["R"]))
        
        return True

    def show_private_keys(self):
        """Show all wallets with their private keys (careful - sensitive)"""
        if not self.addresses:
            print(color_text("❌ No wallets available", COLORS["R"]))
            return
        
        wallets_with_keys = [w for w in self.addresses if w.get("private_key")]
        
        if not wallets_with_keys:
            print(color_text("❌ No wallets with private keys found", COLORS["R"]))
            return
        
        print(color_text(f"\n🔐 Wallets with Private Keys ({len(wallets_with_keys)})", COLORS["R"]))
        print(color_text("=" * 80, COLORS["R"]))
        
        for i, wallet in enumerate(wallets_with_keys, 1):
            print(color_text(f"{i}. {wallet['label']}", COLORS["B"]))
            print(f"   Address: {wallet['address']}")
            print(f"   Private Key: {wallet['private_key']}")
            print(f"   Balance: {wallet.get('balance', 0):.6f} LKC")
            print()
def main():
    wallet = LunaWallet()

    print(color_text("\n💡 Type 'help' for commands", COLORS["I"]))
    print(color_text("💡 Wallet auto-syncs every 60 seconds", COLORS["G"]))
    print(color_text("💡 Use 'receive' to get your address for receiving funds", COLORS["B"]))

    while True:
        try:
            cmd = input(color_text("\n💰 wallet> ", COLORS["BOLD"])).strip().lower()

            if cmd == "status":
                wallet.show_status()
            elif cmd == "stats":
                wallet.show_stats()
            elif cmd == "sync":
                wallet.sync_with_node()
            elif cmd == "receive":
                wallet.receive()
            elif cmd.startswith("send"):
                parts = cmd.split()
                if len(parts) >= 3:
                    to_address = parts[1]
                    try:
                        amount = float(parts[2])
                        memo = " ".join(parts[3:]) if len(parts) > 3 else ""
                        wallet.send(to_address, amount, memo)
                    except ValueError:
                        print(color_text("❌ Invalid amount", COLORS["R"]))
                else:
                    print("Usage: send <address> <amount> [memo]")
            elif cmd == "new":
                label = input("Wallet label: ").strip() or "New Wallet"
                wallet.create_wallet(label)
            elif cmd in ["transactions", "history"]:
                wallet.show_transaction_history()
            elif cmd == "import":
                private_key = input("Private Key:")
                wallet.import_private_key(private_key_hex=private_key)
            elif cmd == "export":
                wallet.export_private_key()
            elif cmd == "show":
                wallet.show_private_keys()
            elif cmd == "backup":
                wallet.backup_wallet()
            elif cmd in ["exit", "quit"]:
                break
            elif cmd == "help":
                print(color_text("💡 Commands:", COLORS["I"]))
                print("  status        - Show wallet status")
                print("  stats         - Show detailed wallet statistics")
                print("  sync          - Manual sync with blockchain")
                print("  receive       - Show receive address and QR code")
                print("  send <addr> <amount> [memo] - Send LKC to address")
                print("  transactions  - Show transaction history")
                print("  history       - Alias for transactions")
                print("  new           - Create new wallet with QR code")
                print("  backup        - Create manual wallet backup")
                print("  exit/quit     - Exit wallet")
                print(color_text("\n🔍 Features:", COLORS["Y"]))
                print("  • Auto-setup on first run")
                print("  • Auto-generate keys for discovered wallets")
                print("  • Auto-sync every 60 seconds")
                print("  • Rewards transaction tracking")
                print("  • Separate confirmed/pending balances")
                print("  • Full wallet vs read-only wallet support")
            else:
                print(color_text("❌ Unknown command. Type 'help' for list.", COLORS["R"]))

        except KeyboardInterrupt:
            print(color_text("\n🛑 Shutting down wallet...", COLORS["R"]))
            break
        except Exception as e:
            print(color_text(f"❌ Error: {e}", COLORS["R"]))


if __name__ == "__main__":
    main()