#!/usr/bin/env python3
"""
Luna Wallet - Integrated with Luna Node Blockchain
"""
import os
import sys
import json
import time
import hashlib
import secrets
import qrcode
from typing import List, Dict
import datetime

# ROYGBIV Color Scheme 🌈
COLORS = {
    'R': '\033[91m', 'O': '\033[93m', 'Y': '\033[93m', 'G': '\033[92m',
    'B': '\033[94m', 'I': '\033[95m', 'V': '\033[95m', 'X': '\033[0m',
    'BOLD': '\033[1m'
}

def color_text(text, color_code):
    return f"{color_code}{text}{COLORS['X']}"

def debug_log(message, category="INFO"):
    """Extensive debug logging"""
    timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    color = COLORS['B'] if category == "INFO" else COLORS['Y'] if category == "DEBUG" else COLORS['R']
    print(f"{color}[{timestamp} {category}]{COLORS['X']} {message}")

class DataManager:
    @staticmethod
    def get_data_dir():
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(base_dir, 'data')
        debug_log(f"Data directory: {data_dir}", "DEBUG")
        return data_dir
    
    @staticmethod
    def save_json(filename, data):
        os.makedirs(DataManager.get_data_dir(), exist_ok=True)
        filepath = os.path.join(DataManager.get_data_dir(), filename)
        debug_log(f"Saving JSON to {filepath}", "DEBUG")
        try:
            with open(filepath, 'w') as f:
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
                with open(filepath, 'r') as f:
                    data = json.load(f)
                debug_log(f"Successfully loaded {filepath}", "DEBUG")
                return data
            except Exception as e:
                debug_log(f"Error loading {filepath}: {e}", "ERROR")
                return default
        debug_log(f"File not found, returning default", "DEBUG")
        return default

class LunaWallet:
    def __init__(self):
        debug_log("Initializing LunaWallet", "INFO")
        self.wallet_file = "wallet.json"
        self.node_data_dir = DataManager.get_data_dir()
        self.addresses = self.load_wallet() or []
        
        if not self.addresses:
            debug_log("No wallet found, creating primary wallet", "INFO")
            self.create_wallet("Primary Wallet")
        
        debug_log("Luna Wallet Initialized", "INFO")
        self.show_status()

    def create_wallet(self, label=""):
        debug_log(f"Creating new wallet with label: {label}", "INFO")
        private_key = secrets.token_hex(32)
        debug_log("Generated private key", "DEBUG")
        public_key = hashlib.sha256(private_key.encode()).hexdigest()
        debug_log("Generated public key", "DEBUG")
        address = f"LKC_{public_key[:16]}_{secrets.token_hex(4)}"
        debug_log(f"Generated address: {address}", "DEBUG")
        
        wallet_data = {
            "address": address,
            "label": label,
            "public_key": public_key,
            "private_key": private_key,
            "balance": 0,
            "transactions": [],
            "created": time.time()
        }
        
        self.addresses.append(wallet_data)
        self.save_wallet()
        
        # Generate QR code
        qr_filename = self.generate_qr_code(address, label)
        
        print(color_text(f"✅ New wallet created: {address}", COLORS['G']))
        print(color_text(f"📄 QR code saved: {qr_filename}", COLORS['B']))
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
            safe_label = "".join(c for c in label if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_label = safe_label.replace(' ', '_')[:20]
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
        # Create backup
        backup_file = f"wallet_backup_{int(time.time())}.json"
        DataManager.save_json(backup_file, self.addresses)
        debug_log(f"Wallet backup created: {backup_file}", "DEBUG")

    def backup_wallet(self):
        """Explicit wallet backup command"""
        debug_log("Creating manual wallet backup", "INFO")
        timestamp = int(time.time())
        backup_file = f"wallet_manual_backup_{timestamp}.json"
        backup_path = os.path.join(DataManager.get_data_dir(), backup_file)
        
        if DataManager.save_json(backup_file, self.addresses):
            print(color_text(f"✅ Wallet backed up to: {backup_path}", COLORS['G']))
            return True
        else:
            print(color_text("❌ Failed to create wallet backup", COLORS['R']))
            return False

    def get_blockchain_data(self):
        """Load blockchain data directly from node's data files"""
        debug_log("Loading blockchain data", "DEBUG")
        try:
            blockchain_file = os.path.join(self.node_data_dir, "blockchain.json")
            debug_log(f"Looking for blockchain file: {blockchain_file}", "DEBUG")
            if os.path.exists(blockchain_file):
                with open(blockchain_file, 'r') as f:
                    data = json.load(f)
                debug_log(f"Blockchain data loaded successfully, type: {type(data)}", "DEBUG")
                return data
            debug_log("Blockchain file not found", "DEBUG")
            return []
        except Exception as e:
            debug_log(f"Error loading blockchain: {e}", "ERROR")
            return []

    def get_node_config(self):
        """Load node configuration"""
        debug_log("Loading node configuration", "DEBUG")
        try:
            config_file = os.path.join(self.node_data_dir, "node_config.json")
            debug_log(f"Looking for config file: {config_file}", "DEBUG")
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    data = json.load(f)
                debug_log("Node config loaded successfully", "DEBUG")
                return data
            debug_log("Node config file not found", "DEBUG")
            return {}
        except Exception as e:
            debug_log(f"Error loading node config: {e}", "ERROR")
            return {}

    def get_address_balance(self, address):
        """Calculate balance for an address by scanning the blockchain"""
        debug_log(f"Calculating balance for address: {address}", "DEBUG")
        blockchain_data = self.get_blockchain_data()
        if not blockchain_data:
            debug_log("No blockchain data available", "DEBUG")
            return 0
        
        balance = 0
        debug_log(f"Blockchain data type: {type(blockchain_data)}", "DEBUG")
        
        # Handle different blockchain data structures
        if isinstance(blockchain_data, list):
            chain = blockchain_data
            debug_log(f"Processing as list with {len(chain)} items", "DEBUG")
        elif isinstance(blockchain_data, dict) and 'chain' in blockchain_data:
            chain = blockchain_data['chain']
            debug_log("Processing as dict with 'chain' key", "DEBUG")
        elif isinstance(blockchain_data, dict) and 'blocks' in blockchain_data:
            chain = blockchain_data['blocks']
            debug_log("Processing as dict with 'blocks' key", "DEBUG")
        else:
            # Try to find any list in the dictionary
            chain = []
            for key, value in blockchain_data.items():
                if isinstance(value, list):
                    chain = value
                    debug_log(f"Found list in key: {key}", "DEBUG")
                    break
        
        debug_log(f"Final chain length: {len(chain)}", "DEBUG")
        
        # Scan all blocks for transactions involving this address
        for block_index, block in enumerate(chain):
            debug_log(f"Processing block {block_index}", "DEBUG")
            # Extract transactions from block
            transactions = []
            if isinstance(block, dict):
                if 'transactions' in block:
                    transactions = block['transactions']
                    debug_log(f"Found {len(transactions)} transactions in block", "DEBUG")
                elif 'data' in block and isinstance(block['data'], list):
                    transactions = block['data']
                    debug_log(f"Found {len(transactions)} data items in block", "DEBUG")
            elif hasattr(block, 'transactions'):
                transactions = block.transactions
                debug_log(f"Found {len(transactions)} transactions in block object", "DEBUG")
            
            if not isinstance(transactions, list):
                debug_log("No transactions list found in block", "DEBUG")
                continue
                
            for tx_index, tx in enumerate(transactions):
                if not isinstance(tx, dict):
                    debug_log(f"Transaction {tx_index} is not a dict, skipping", "DEBUG")
                    continue
                    
                # Mining reward
                if tx.get('to') == address:
                    amount = tx.get('amount', 0)
                    balance += amount
                    debug_log(f"Found mining reward: +{amount} LKC", "DEBUG")
                # Regular transaction
                if tx.get('from') == address:
                    amount = tx.get('amount', 0)
                    balance -= amount
                    debug_log(f"Found outgoing transaction: -{amount} LKC", "DEBUG")
                if tx.get('to') == address:
                    amount = tx.get('amount', 0)
                    balance += amount
                    debug_log(f"Found incoming transaction: +{amount} LKC", "DEBUG")
        
        debug_log(f"Final balance for {address}: {balance} LKC", "DEBUG")
        return balance

    def sync_with_node(self):
        """Sync wallet with blockchain data from node's files"""
        debug_log("Starting sync with node", "INFO")
        
        blockchain_data = self.get_blockchain_data()
        if not blockchain_data:
            print(color_text("❌ No blockchain data found - make sure luna_node.py has been run", COLORS['R']))
            return False
        
        # Determine chain length
        if isinstance(blockchain_data, list):
            chain_height = len(blockchain_data)
        else:
            chain_height = 0
            
        debug_log(f"Blockchain height: {chain_height}", "DEBUG")
        print(color_text(f"📊 Blockchain data loaded: {chain_height} blocks", COLORS['I']))
        
        # Update balances for all addresses
        for wallet in self.addresses:
            address = wallet['address']
            debug_log(f"Syncing wallet: {address}", "DEBUG")
            balance = self.get_address_balance(address)
            transactions = self.get_address_transactions(address)
            
            wallet['balance'] = balance
            wallet['transactions'] = transactions
            
            print(color_text(f"✅ Synced {address}: {balance} LKC, {len(transactions)} transactions", COLORS['G']))
        
        self.save_wallet()
        debug_log("Sync completed successfully", "INFO")
        print(color_text("✅ Sync completed", COLORS['G']))
        return True

    def get_address_transactions(self, address):
        """Get all transactions for an address"""
        debug_log(f"Getting transactions for address: {address}", "DEBUG")
        blockchain_data = self.get_blockchain_data()
        if not blockchain_data:
            debug_log("No blockchain data available", "DEBUG")
            return []
        
        transactions = []
        
        # Handle different blockchain data structures
        if isinstance(blockchain_data, list):
            chain = blockchain_data
            debug_log("Processing blockchain as list", "DEBUG")
        elif isinstance(blockchain_data, dict) and 'chain' in blockchain_data:
            chain = blockchain_data['chain']
            debug_log("Processing blockchain as dict with 'chain' key", "DEBUG")
        else:
            chain = []
            debug_log("Unknown blockchain structure", "DEBUG")
        
        debug_log(f"Processing {len(chain)} blocks", "DEBUG")
        
        for block in chain:
            # Extract block info
            block_index = 0
            block_timestamp = time.time()
            
            if isinstance(block, dict):
                block_index = block.get('index', 0)
                block_timestamp = block.get('timestamp', time.time())
                block_txs = block.get('transactions', [])
                debug_log(f"Block {block_index} has {len(block_txs)} transactions", "DEBUG")
            else:
                block_txs = []
                debug_log("Block is not a dictionary, skipping", "DEBUG")
            
            for tx in block_txs:
                if not isinstance(tx, dict):
                    debug_log("Transaction is not a dictionary, skipping", "DEBUG")
                    continue
                    
                if tx.get('from') == address or tx.get('to') == address:
                    tx_copy = tx.copy()
                    tx_copy['block_height'] = block_index
                    tx_copy['timestamp'] = block_timestamp
                    tx_copy['status'] = 'confirmed'
                    transactions.append(tx_copy)
                    debug_log(f"Found relevant transaction in block {block_index}", "DEBUG")
        
        debug_log(f"Found {len(transactions)} total transactions", "DEBUG")
        return transactions

    def send(self, to_address, amount, memo="No Memo."):
        """Create a transaction and broadcast it to the network"""
        debug_log(f"Sending {amount} LKC to {to_address}", "INFO")
        if not self.addresses:
            print(color_text("❌ No wallets available", COLORS['R']))
            return False
        
        from_wallet = self.addresses[0]
        debug_log(f"Using wallet: {from_wallet['address']}", "DEBUG")
        
        # Check balance (include pending outbound transactions)
        available_balance = self.get_available_balance(from_wallet['address'])
        debug_log(f"Available balance: {available_balance} LKC", "DEBUG")
        if available_balance < amount:
            print(color_text(f"❌ Insufficient balance: {available_balance} LKC available, {amount} LKC requested", COLORS['R']))
            return False
        
        # Create transaction with unique ID
        transaction_id = f"tx_{secrets.token_hex(16)}"
        debug_log(f"Generated transaction ID: {transaction_id}", "DEBUG")
        transaction = {
            "type": "transfer",
            "from": from_wallet['address'],
            "to": to_address,
            "amount": amount,
            "memo": memo,
            "timestamp": time.time(),
            "signature": transaction_id,
            "hash": hashlib.sha256(f"{from_wallet['address']}{to_address}{amount}{time.time()}".encode()).hexdigest(),
            "status": "pending",
            "confirmations": 0
        }
        
        # Save to local pending transactions
        pending_tx = {
            "hash": transaction['hash'],
            "signature": transaction_id,
            "from": from_wallet['address'],
            "to": to_address,
            "amount": amount,
            "memo": memo,
            "timestamp": time.time(),
            "status": "pending",
            "confirmations": 0,
            "block_height": None
        }
        
        from_wallet['transactions'].append(pending_tx)
        self.save_wallet()
        debug_log("Transaction saved to local wallet", "DEBUG")
        
        # Broadcast to network via API
        if self.broadcast_transaction(transaction):
            print(color_text(f"✅ Transaction created: {amount} LKC to {to_address}", COLORS['G']))
            print(color_text(f"📄 Transaction ID: {transaction_id}", COLORS['B']))
            print(color_text("⏳ Waiting for confirmation...", COLORS['Y']))
            return True
        else:
            # Mark as failed if broadcast fails
            pending_tx['status'] = 'failed'
            self.save_wallet()
            print(color_text("❌ Failed to broadcast transaction", COLORS['R']))
            return False

    def broadcast_transaction(self, transaction):
        """Broadcast transaction to the blockchain API"""
        debug_log("Broadcasting transaction to network", "INFO")
        try:
            import requests
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

    def get_available_balance(self, address):
        """Get available balance (excluding pending outbound transactions)"""
        debug_log(f"Calculating available balance for {address}", "DEBUG")
        confirmed_balance = self.get_address_balance(address)
        debug_log(f"Confirmed balance: {confirmed_balance} LKC", "DEBUG")
        
        # Subtract pending outbound transactions
        pending_outbound = sum(
            tx['amount'] for tx in self.get_pending_transactions(address) 
            if tx['from'] == address and tx['status'] == 'pending'
        )
        debug_log(f"Pending outbound: {pending_outbound} LKC", "DEBUG")
        
        available = max(0, confirmed_balance - pending_outbound)
        debug_log(f"Available balance: {available} LKC", "DEBUG")
        return available

    def get_pending_transactions(self, address):
        """Get pending transactions for an address"""
        debug_log(f"Getting pending transactions for {address}", "DEBUG")
        pending = []
        for wallet in self.addresses:
            if wallet['address'] == address:
                for tx in wallet['transactions']:
                    if tx.get('status') == 'pending':
                        pending.append(tx)
        debug_log(f"Found {len(pending)} pending transactions", "DEBUG")
        return pending

    def update_transaction_confirmations(self):
        """Update confirmation counts for all transactions"""
        debug_log("Updating transaction confirmations", "DEBUG")
        
        blockchain_data = self.get_blockchain_data()
        if not blockchain_data:
            debug_log("No blockchain data available", "DEBUG")
            return
        
        # Find the current blockchain height
        if isinstance(blockchain_data, list):
            current_height = len(blockchain_data)
        else:
            current_height = 0
        
        debug_log(f"Current blockchain height: {current_height}", "DEBUG")
        updated = False
        
        for wallet_index, wallet in enumerate(self.addresses):
            debug_log(f"Processing wallet {wallet_index}: {wallet['address']}", "DEBUG")
            for tx_index, tx in enumerate(wallet['transactions']):
                if tx.get('status') in ['pending', 'confirmed']:
                    tx_hash = tx.get('hash')
                    block_height = tx.get('block_height')
                    debug_log(f"Transaction {tx_index}: hash={tx_hash}, block_height={block_height}", "DEBUG")
                    
                    if block_height and current_height > 0:
                        confirmations = current_height - block_height
                        tx['confirmations'] = confirmations
                        debug_log(f"Confirmations: {confirmations}", "DEBUG")
                        
                        # Update status based on confirmations
                        if confirmations >= 6:  # 6 confirmations = fully confirmed
                            if tx['status'] != 'confirmed':
                                tx['status'] = 'confirmed'
                                updated = True
                                debug_log("Transaction fully confirmed (6+ confirmations)", "DEBUG")
                        elif confirmations > 0 and tx['status'] == 'pending':
                            tx['status'] = 'confirmed'  # At least 1 confirmation
                            updated = True
                            debug_log("Transaction confirmed (1+ confirmations)", "DEBUG")
        
        if updated:
            self.save_wallet()
            debug_log("Transaction confirmations updated and saved", "DEBUG")

    def show_transaction_history(self):
        """Show comprehensive transaction history with status icons and confirmations"""
        debug_log("Displaying transaction history", "INFO")
        if not self.addresses:
            print(color_text("❌ No wallets available", COLORS['R']))
            return
        
        # Update confirmations first
        self.update_transaction_confirmations()
        
        wallet_address = self.addresses[0]['address']
        transactions = sorted(
            self.addresses[0]['transactions'], 
            key=lambda x: x.get('timestamp', 0), 
            reverse=True
        )
        
        print(color_text(f"\n📊 Transaction History for {self.addresses[0]['label']}:", COLORS['B']))
        print("=" * 80)
        
        if not transactions:
            print(color_text("No transactions found", COLORS['O']))
            return
        
        for i, tx in enumerate(transactions, 1):
            status = tx.get('status', 'unknown')
            confirmations = tx.get('confirmations', 0)
            
            # Status icons and colors with confirmation info
            if status == 'confirmed':
                if confirmations >= 6:
                    status_icon = "✅"  # Fully confirmed
                    status_text = f"CONFIRMED ({confirmations} confirmations)"
                else:
                    status_icon = "🟡"  # Partially confirmed
                    status_text = f"CONFIRMED ({confirmations}/6 confirmations)"
                status_color = COLORS['G']
            elif status == 'pending':
                status_icon = "⏳"
                status_text = "PENDING (0 confirmations)"
                status_color = COLORS['Y']
            elif status == 'failed':
                status_icon = "❌"
                status_text = "FAILED"
                status_color = COLORS['R']
            else:
                status_icon = "❓"
                status_text = "UNKNOWN"
                status_color = COLORS['R']
            
            # Direction and amount
            if tx.get('from') == wallet_address:
                direction = "➡️ OUTGOING"
                amount_color = COLORS['R']
            else:
                direction = "⬅️ INCOMING" 
                amount_color = COLORS['G']
            
            amount = tx.get('amount', 0)
            memo = tx.get('memo', '')
            
            print(f"{i}. {status_color}{status_icon} {direction} {amount} LKC{COLORS['X']}")
            print(f"   To/From: {tx.get('to' if direction == '➡️ OUTGOING' else 'from')}")
            print(f"   Status: {status_color}{status_text}{COLORS['X']}")
            
            if memo:
                print(f"   Memo: {memo}")
            
            print(f"   Time: {datetime.datetime.fromtimestamp(tx.get('timestamp', 0))}")
            print(f"   Hash: {tx.get('hash', 'N/A')[:20]}...")
            print()

    def show_status(self):
        """Display wallet and blockchain status"""
        debug_log("Displaying wallet status", "INFO")
        print(color_text("\n" + "="*60, COLORS['I']))
        print(color_text("                 LUNA WALLET STATUS", COLORS['BOLD']))
        print(color_text("="*60, COLORS['I']))
        
        # Check if node data exists
        blockchain_data = self.get_blockchain_data()
        node_config = self.get_node_config()
        
        node_status = "🟢 Data Found" if blockchain_data else "🔴 No Data"
        print(color_text(f"🌐 Node Status: {node_status}", COLORS['G' if blockchain_data else 'R']))
        
        # Get blockchain info
        if isinstance(blockchain_data, list):
            chain_height = len(blockchain_data)
        else:
            chain_height = 0
            
        total_balance = sum(wallet['balance'] for wallet in self.addresses)
        print(color_text(f"💰 Total Balance: {total_balance} LKC", COLORS['Y']))
        print(color_text(f"👛 Wallets: {len(self.addresses)}", COLORS['B']))
        print(color_text(f"⛓️  Blockchain Height: {chain_height}", COLORS['I']))
        
        # Show miner address from node config if available
        if node_config.get('miner_address'):
            print(color_text(f"⛏️  Node Miner: {node_config['miner_address']}", COLORS['O']))
        
        for i, wallet in enumerate(self.addresses):
            color = [COLORS['G'], COLORS['B'], COLORS['Y'], COLORS['I']][i % 4]
            print(color_text(f"\n{i+1}. {wallet['label']}", color))
            print(color_text(f"   Address: {wallet['address']}", color))
            print(color_text(f"   Balance: {wallet['balance']} LKC", color))
            print(color_text(f"   Transactions: {len(wallet['transactions'])}", color))

def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    wallet = LunaWallet()
    
    print(color_text("\n💡 Type 'help' for commands", COLORS['I']))
    print(color_text("💡 Wallet transactions will be broadcast to the blockchain!", COLORS['Y']))
    
    # Start background confirmation checker
    import threading
    import time
    
    def confirmation_checker():
        while True:
            try:
                time.sleep(30)  # Check every 30 seconds
                # Clear any existing output and show the prompt at bottom
                print("\r🔍 Checking transaction confirmations...", end="")
                time.sleep(0.5)
                print("\r" + " " * 50, end="")  # Clear line
                print("\r", end="")
                wallet.update_transaction_confirmations()
            except Exception as e:
                debug_log(f"Confirmation checker error: {e}", "ERROR")
    
    checker_thread = threading.Thread(target=confirmation_checker, daemon=True)
    checker_thread.start()
    
    while True:
        try:
            # Always ensure prompt is at bottom
            cmd = input(color_text("\n💰 wallet> ", COLORS['BOLD'])).strip().lower()
            
            if cmd == "status":
                wallet.show_status()
                
            elif cmd == "sync":
                wallet.sync_with_node()
                wallet.update_transaction_confirmations()
                
            elif cmd.startswith("send"):
                parts = cmd.split()
                if len(parts) >= 3:
                    to_address = parts[1]
                    try:
                        amount = float(parts[2])
                        memo = " ".join(parts[3:]) if len(parts) > 3 else ""
                        if wallet.send(to_address, amount, memo):
                            time.sleep(2)
                            wallet.update_transaction_confirmations()
                    except ValueError:
                        print(color_text("❌ Invalid amount", COLORS['R']))
                else:
                    print("Usage: send <address> <amount> [memo]")
                    
            elif cmd == "new":
                label = input("Wallet label: ").strip() or "New Wallet"
                wallet.create_wallet(label)
                
            elif cmd in ["transactions", "history"]:
                wallet.show_transaction_history()
                
            elif cmd == "backup":
                wallet.backup_wallet()
                
            elif cmd in ["exit", "quit"]:
                break
                
            elif cmd == "help":
                print(color_text("💡 Commands:", COLORS['I']))
                print("  status        - Show wallet status")
                print("  sync          - Sync with blockchain")
                print("  send <addr> <amount> [memo] - Send LKC to address")
                print("  transactions  - Show transaction history with confirmations")
                print("  history       - Alias for transactions")
                print("  new           - Create new wallet with QR code")
                print("  backup        - Create manual wallet backup")
                print("  exit/quit     - Exit wallet")
                print(color_text("\n🔗 Transactions are broadcast to the blockchain network", COLORS['Y']))
                print(color_text("⏳ Confirmations update automatically every 30 seconds", COLORS['G']))
                print(color_text("📊 Transaction history shows status icons and confirmation counts", COLORS['B']))
                
            else:
                print(color_text("❌ Unknown command. Type 'help' for list.", COLORS['R']))
                
        except KeyboardInterrupt:
            print(color_text("\n🛑 Shutting down wallet...", COLORS['R']))
            break
        except Exception as e:
            print(color_text(f"❌ Error: {e}", COLORS['R']))

if __name__ == "__main__":
    main()