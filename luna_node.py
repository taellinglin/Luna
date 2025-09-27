#!/usr/bin/env python3
"""
Luna Node - Enhanced with Mempool Scanning and Merging
"""
import os
import sys
import json
import time
import threading
import socket
import hashlib
import uuid
import requests
from typing import List, Dict, Set
import atexit

# ROYGBIV Color Scheme 🌈
COLORS = {
    'R': '\033[91m',  # Red
    'O': '\033[93m',  # Yellow/Orange
    'Y': '\033[93m',  # Yellow
    'G': '\033[92m',  # Green
    'B': '\033[94m',  # Blue
    'I': '\033[95m',  # Magenta/Indigo
    'V': '\033[95m',  # Violet
    'X': '\033[0m',   # Reset
    'BOLD': '\033[1m'
}

def color_text(text, color_code):
    return f"{color_code}{text}{COLORS['X']}"

class ConfigManager:
    @staticmethod
    def get_data_dir():
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_dir, 'data')
    
    @staticmethod
    def save_json(filename, data):
        os.makedirs(ConfigManager.get_data_dir(), exist_ok=True)
        filepath = os.path.join(ConfigManager.get_data_dir(), filename)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    
    @staticmethod
    def load_json(filename, default=None):
        if default is None:
            default = {}
        filepath = os.path.join(ConfigManager.get_data_dir(), filename)
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
        return default

class NodeConfig:
    def __init__(self):
        self.config_file = "node_config.json"
        self.load_config()
    
    def load_config(self):
        config = ConfigManager.load_json(self.config_file, {
            "node_id": str(uuid.uuid4()),
            "miner_address": "",
            "difficulty": 4,
            "mining_reward": 1,  # Base reward of 1
            "node_version": "1.0.0",
            "created_at": time.time(),
            "last_sync": 0,
            "bills_mined": [],
            "verification_links": {},
            "auto_mine": False,
            "peer_port": 9333,
            "mined_transactions": {},  # Ensure this is a dict, not a list
            "api_base_url": "https://bank.linglin.art",
            "mempool_file": "mempool.json",
            "last_mempool_sync": 0
        })
        
        # Force mined_transactions to be a dict if it was saved as something else
        if not isinstance(config.get("mined_transactions"), dict):
            print(color_text("⚠️  Fixing mined_transactions type from list to dict", COLORS['O']))
            config["mined_transactions"] = {}
        
        self.node_id = config["node_id"]
        self.miner_address = config["miner_address"]
        self.difficulty = config["difficulty"]
        self.mining_reward = config["mining_reward"]
        self.node_version = config["node_version"]
        self.created_at = config["created_at"]
        self.last_sync = config["last_sync"]
        self.bills_mined = config["bills_mined"]
        self.verification_links = config["verification_links"]
        self.auto_mine = config["auto_mine"]
        self.peer_port = config["peer_port"]
        self.mined_transactions = config["mined_transactions"]  # This is now guaranteed to be a dict
        self.api_base_url = config["api_base_url"]
        self.mempool_file = config["mempool_file"]
        self.last_mempool_sync = config["last_mempool_sync"]
    
    def generate_miner_address(self):
        """Generate a unique miner address based on node ID"""
        base_hash = hashlib.sha256(f"{self.node_id}{time.time()}".encode()).hexdigest()
        return f"LUN_{base_hash[:16]}"
    
    def save_config(self):
        config = {
            "node_id": self.node_id,
            "miner_address": self.miner_address,
            "difficulty": self.difficulty,
            "mining_reward": self.mining_reward,
            "node_version": self.node_version,
            "created_at": self.created_at,
            "last_sync": time.time(),
            "bills_mined": self.bills_mined,
            "verification_links": self.verification_links,
            "auto_mine": self.auto_mine,
            "peer_port": self.peer_port,
            "mined_transactions": self.mined_transactions,
            "api_base_url": self.api_base_url,
            "mempool_file": self.mempool_file,
            "last_mempool_sync": self.last_mempool_sync
        }
        ConfigManager.save_json(self.config_file, config)
    
    def add_bill(self, block_hash, amount, timestamp, verification_url="", transaction_count=0):
        """Add a mined bill to history"""
        bill = {
            "block_hash": block_hash,
            "amount": amount,
            "timestamp": timestamp,
            "date": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp)),
            "verification_url": verification_url,
            "transactions_mined": transaction_count
        }
        self.bills_mined.append(bill)
        
        # Store verification link
        if verification_url:
            self.verification_links[block_hash] = verification_url
        
        # Keep only last 100 bills
        if len(self.bills_mined) > 100:
            self.bills_mined = self.bills_mined[-100:]
        
        self.save_config()
    
    def get_bills_summary(self):
        """Get summary of mined bills"""
        total_bills = len(self.bills_mined)
        total_reward = sum(bill["amount"] for bill in self.bills_mined)
        total_transactions = sum(bill.get("transactions_mined", 0) for bill in self.bills_mined)
        return total_bills, total_reward, total_transactions
    
    def update_difficulty(self, new_difficulty):
        """Update difficulty with validation"""
        if 1 <= new_difficulty <= 8:
            self.difficulty = new_difficulty
            self.save_config()
            return True
        return False
    
    def mark_transaction_mined(self, tx_signature, block_hash):
        """Mark a transaction as already mined"""
        print(color_text(f"🔍 [DEBUG] START: mark_transaction_mined", COLORS['B']))
        print(color_text(f"🔍 [DEBUG] tx_signature: {tx_signature[:20]}...", COLORS['B']))
        print(color_text(f"🔍 [DEBUG] block_hash: {block_hash[:20]}...", COLORS['B']))
        print(color_text(f"🔍 [DEBUG] mined_transactions type: {type(self.mined_transactions)}", COLORS['B']))
        
        # Ensure mined_transactions is a dictionary
        if not isinstance(self.mined_transactions, dict):
            print(color_text(f"⚠️  mined_transactions is {type(self.mined_transactions)}, converting to dict", COLORS['O']))
            print(color_text(f"🔍 [DEBUG] Current mined_transactions value: {self.mined_transactions}", COLORS['O']))
            
            # Convert to dict if it's a list or other type
            if isinstance(self.mined_transactions, list):
                # Convert list to dict
                new_mined_txs = {}
                for i, item in enumerate(self.mined_transactions):
                    if isinstance(item, dict) and 'signature' in item:
                        # If list contains transaction objects, use their signature as key
                        new_mined_txs[item['signature']] = {
                            "block_hash": item.get('block_hash', 'unknown'),
                            "timestamp": item.get('timestamp', time.time())
                        }
                    else:
                        # Create a placeholder key
                        new_mined_txs[f"converted_{i}"] = {
                            "block_hash": "converted",
                            "timestamp": time.time()
                        }
                self.mined_transactions = new_mined_txs
                print(color_text(f"🔍 [DEBUG] Converted list to dict with {len(new_mined_txs)} entries", COLORS['G']))
            else:
                # Initialize as empty dict for any other type
                self.mined_transactions = {}
                print(color_text("🔍 [DEBUG] Initialized empty dict for mined_transactions", COLORS['G']))
        
        # Now safely add the transaction
        print(color_text(f"🔍 [DEBUG] Adding to mined_transactions (current size: {len(self.mined_transactions)})", COLORS['B']))
        self.mined_transactions[tx_signature] = {
            "block_hash": block_hash,
            "timestamp": time.time()
        }
        print(color_text(f"🔍 [DEBUG] Added successfully (new size: {len(self.mined_transactions)})", COLORS['G']))
        
        self.save_config()
        print(color_text("🔍 [DEBUG] Config saved", COLORS['G']))
        print(color_text("🔍 [DEBUG] END: mark_transaction_mined - SUCCESS", COLORS['G']))
    
    def is_transaction_mined(self, tx_signature):
        """Check if a transaction has already been rewarded"""
        # Ensure mined_transactions is a dictionary
        if not isinstance(self.mined_transactions, dict):
            print(color_text(f"⚠️  mined_transactions is {type(self.mined_transactions)} in is_transaction_mined, returning False", COLORS['O']))
            return False
        
        return tx_signature in self.mined_transactions

class Block:
    def __init__(self, index, previous_hash, transactions, nonce=0, timestamp=None):
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp or time.time()
        self.transactions = transactions
        self.nonce = nonce
        self.hash = self.calculate_hash()
        self.mining_time = 0

    def calculate_hash(self):
        block_data = f"{self.index}{self.previous_hash}{self.timestamp}{json.dumps(self.transactions, sort_keys=True)}{self.nonce}"
        return hashlib.sha256(block_data.encode()).hexdigest()

    def to_dict(self):
        """Convert block to dictionary for JSON storage"""
        return {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "nonce": self.nonce,
            "hash": self.hash,
            "mining_time": self.mining_time
        }

    @staticmethod
    def from_dict(block_dict):
        """Create Block object from dictionary with proper error handling"""
        try:
            # Validate and convert each field with proper error handling
            index = block_dict.get("index", 0)
            if not isinstance(index, int):
                print(f"⚠️  Invalid index type: {type(index)}, converting to int")
                try:
                    index = int(index)
                except (ValueError, TypeError):
                    index = 0
            
            previous_hash = block_dict.get("previous_hash", "0")
            if not isinstance(previous_hash, str):
                print(f"⚠️  Invalid previous_hash type: {type(previous_hash)}, converting to str")
                previous_hash = str(previous_hash)
            
            transactions = block_dict.get("transactions", [])
            if not isinstance(transactions, list):
                print(f"⚠️  Invalid transactions type: {type(transactions)}, using empty list")
                transactions = []
            
            nonce = block_dict.get("nonce", 0)
            if not isinstance(nonce, int):
                print(f"⚠️  Invalid nonce type: {type(nonce)}, converting to int")
                try:
                    nonce = int(nonce)
                except (ValueError, TypeError):
                    nonce = 0
            
            timestamp = block_dict.get("timestamp")
            if timestamp is not None and not isinstance(timestamp, (int, float)):
                print(f"⚠️  Invalid timestamp type: {type(timestamp)}, using current time")
                timestamp = time.time()
            
            # Create the block
            block = Block(index, previous_hash, transactions, nonce, timestamp)
            
            # Set the hash if provided and valid
            if "hash" in block_dict and isinstance(block_dict["hash"], str):
                block.hash = block_dict["hash"]
            
            # Set mining time if provided
            if "mining_time" in block_dict and isinstance(block_dict["mining_time"], (int, float)):
                block.mining_time = block_dict["mining_time"]
            
            return block
            
        except Exception as e:
            print(f"❌ Error creating block from dict: {e}")
            print(f"📋 Problematic block data: {json.dumps(block_dict, indent=2)[:500]}...")
            # Return a default block to prevent crashes
            return Block(0, "0", [{"type": "error", "message": f"Failed to load block: {e}"}])

    def mine_block(self, difficulty, progress_callback=None):
        target = "0" * difficulty
        start_time = time.time()
        hashes_tried = 0
        hash_rates = []
        last_update = start_time
        
        print(color_text(f"\n🎯 Mining Block #{self.index} | Difficulty: {difficulty}", COLORS['B']))
        print(color_text("⛏️  Starting mining operation...", COLORS['G']))
        print("=" * 60)
        
        while self.hash[:difficulty] != target:
            self.nonce += 1
            hashes_tried += 1
            self.hash = self.calculate_hash()
            
            current_time = time.time()
            if current_time - last_update >= 0.5:
                elapsed = current_time - start_time
                current_hash_rate = hashes_tried / elapsed
                hash_rates.append(current_hash_rate)
                avg_hash_rate = sum(hash_rates[-10:]) / min(10, len(hash_rates))
                
                # ROYGBIV progress display
                progress = min(self.nonce / (16 ** difficulty), 0.99)
                color_idx = int(progress * 6) % 6
                color = [COLORS['R'], COLORS['O'], COLORS['Y'], COLORS['G'], COLORS['B'], COLORS['I']][color_idx]
                
                filled = int(30 * progress)
                progress_bar = f"{color}[{'█' * filled}{'░' * (30-filled)}]{COLORS['X']}"
                
                hash_rate_str = f"{avg_hash_rate/1000:.1f} kH/s" if avg_hash_rate > 1000 else f"{avg_hash_rate:.1f} H/s"
                
                print(f"\r{color}⛏️  {progress_bar} {progress:.1%} | {hash_rate_str} | Nonce: {self.nonce:,}{COLORS['X']}", end="")
                last_update = current_time
                
                if progress_callback:
                    progress_callback(hashes_tried, avg_hash_rate, progress)
        
        self.mining_time = time.time() - start_time
        print(color_text(f"\n✅ Block mined in {self.mining_time:.2f}s | Hash: {self.hash[:16]}...", COLORS['G']))
        return True

class Blockchain:
    def __init__(self, config):
        self.config = config
        self.chain_file = "blockchain.json"
        self.mempool_file = config.mempool_file
        self.chain = self.load_chain() or [self.create_genesis_block()]
        self.pending_transactions = []
        self.mempool = self.load_mempool()  # Load local mempool
        self.peers = set()
        self.is_mining = False
        
        # Auto-sync on startup
        threading.Thread(target=self.auto_sync, daemon=True).start()

    def create_genesis_block(self):
        return Block(0, "0", [{
            "type": "genesis",
            "message": "Luna Genesis Block",
            "timestamp": time.time(),
            "reward": 1000,
            "miner": "network"
        }])

    def load_chain(self):
        """Load blockchain from local storage - always return list of Block objects"""
        chain_data = ConfigManager.load_json(self.chain_file)
        if not chain_data:
            return None
            
        blocks = self._load_blocks_from_data(chain_data)
        # Ensure we return a list of Block objects
        if blocks:
            block_objects = []
            for block in blocks:
                if isinstance(block, Block):
                    block_objects.append(block)
                elif isinstance(block, dict):
                    try:
                        block_obj = Block.from_dict(block)
                        block_objects.append(block_obj)
                    except Exception as e:
                        print(color_text(f"❌ Error converting block: {e}", COLORS['R']))
                        continue
            return block_objects
        return None

    def load_mempool(self):
        """Load mempool - prefer blockchain.mempool, fall back to local file"""
        try:
            # First priority: Use blockchain's mempool if it exists and has data
            if hasattr(self, 'mempool') and self.mempool is not None:
                if isinstance(self.mempool, list) and len(self.mempool) > 0:
                    print(color_text(f"📋 Using blockchain mempool ({len(self.mempool)} transactions)", COLORS['G']))
                    return self.mempool
            
            # Second priority: Load from local file
            mempool_data = ConfigManager.load_json(self.mempool_file, [])
            if isinstance(mempool_data, list) and len(mempool_data) > 0:
                print(color_text(f"📋 Loaded {len(mempool_data)} transactions from local mempool file", COLORS['G']))
                
                # Also update blockchain.mempool if it exists
                if hasattr(self, 'mempool'):
                    self.mempool = mempool_data
                    print(color_text("🔄 Updated blockchain mempool from local file", COLORS['B']))
                
                return mempool_data
            else:
                print(color_text("📭 Local mempool file is empty or invalid", COLORS['O']))
                
                # Initialize empty mempool in blockchain if it exists
                if hasattr(self, 'mempool'):
                    self.mempool = []
                
                return []
                
        except Exception as e:
            print(color_text(f"❌ Error loading mempool: {e}", COLORS['R']))
            
            # Fallback: return empty list and ensure blockchain.mempool exists
            if hasattr(self, 'mempool'):
                self.mempool = []
            
            return []

    def save_mempool(self):
        """Save mempool to local file and update blockchain.mempool"""
        try:
            # Get current mempool data
            if hasattr(self, 'mempool') and self.mempool is not None:
                mempool_to_save = self.mempool
            else:
                mempool_to_save = self.mempool  # Fallback to instance attribute
            
            # Save to file
            ConfigManager.save_json(self.mempool_file, mempool_to_save)
            print(color_text(f"💾 Saved {len(mempool_to_save)} transactions to local mempool", COLORS['G']))
            
            # Ensure both locations are synchronized
            if hasattr(self, 'mempool'):
                self.mempool = mempool_to_save
            self.mempool = mempool_to_save  # Update instance attribute
            
            return True
        except Exception as e:
            print(color_text(f"❌ Error saving mempool: {e}", COLORS['R']))
            return False

    def get_mempool(self):
        """Get current mempool - unified access point"""
        # Priority 1: blockchain.mempool
        if hasattr(self, 'mempool') and self.mempool is not None:
            return self.mempool
        
        # Priority 2: instance mempool
        if hasattr(self, 'mempool') and self.mempool is not None:
            return self.mempool
        
        # Priority 3: load from file
        return self.load_mempool()

    def update_mempool(self, new_mempool):
        """Update mempool in all locations"""
        try:
            # Update blockchain mempool if it exists
            if hasattr(self, 'mempool'):
                self.mempool = new_mempool
            
            # Update instance mempool
            self.mempool = new_mempool
            
            # Save to file
            ConfigManager.save_json(self.mempool_file, new_mempool)
            
            print(color_text(f"🔄 Updated mempool to {len(new_mempool)} transactions", COLORS['G']))
            return True
        except Exception as e:
            print(color_text(f"❌ Error updating mempool: {e}", COLORS['R']))
            return False

    def sync_mempool_from_api(self):
        """Sync mempool from API and update all locations"""
        try:
            print(color_text("🌐 Syncing mempool from API...", COLORS['B']))
            response = requests.get(f"{self.config.api_base_url}/mempool", timeout=30)
            
            if response.status_code == 200:
                api_mempool = response.json()
                
                if isinstance(api_mempool, list):
                    print(color_text(f"📥 Downloaded {len(api_mempool)} transactions from API", COLORS['G']))
                    
                    # Get current mempool
                    current_mempool = self.get_mempool()
                    
                    # Merge mempools
                    merged_mempool = self.merge_mempools(current_mempool, api_mempool)
                    new_transactions = len(merged_mempool) - len(current_mempool)
                    
                    if new_transactions > 0:
                        # Update all mempool locations
                        self.update_mempool(merged_mempool)
                        
                        self.config.last_mempool_sync = time.time()
                        self.config.save_config()
                        
                        print(color_text(f"✅ Added {new_transactions} new transactions", COLORS['G']))
                        
                        # Show Genesis transactions if any
                        genesis_txs = [tx for tx in merged_mempool if tx.get('type') == 'GTX_Genesis']
                        if genesis_txs:
                            print(color_text(f"💰 Found {len(genesis_txs)} Genesis transactions!", COLORS['Y']))
                        
                        return True
                    else:
                        print(color_text("ℹ️  Mempool is already up to date", COLORS['B']))
                        return True
                else:
                    print(color_text("❌ Invalid mempool format from API", COLORS['R']))
            else:
                print(color_text(f"❌ API returned status {response.status_code}", COLORS['R']))
                
        except Exception as e:
            print(color_text(f"❌ Sync failed: {e}", COLORS['R']))
        
        return False
    
    def _load_blocks_from_data(self, chain_data):
        """Load blocks from various data formats - return mixed list"""
        if isinstance(chain_data, list):
            return self._process_block_list(chain_data)
        elif isinstance(chain_data, dict):
            # Handle different possible structures
            if 'blocks' in chain_data and isinstance(chain_data['blocks'], list):
                return self._process_block_list(chain_data['blocks'])
            elif 'chain' in chain_data and isinstance(chain_data['chain'], list):
                return self._process_block_list(chain_data['chain'])
            else:
                # If it's a dict but not the expected structure, try to extract blocks
                for key, value in chain_data.items():
                    if isinstance(value, list) and key not in ['peers', 'pending_transactions']:
                        print(f"🔍 Found potential block list in key: {key}")
                        return self._process_block_list(value)
        
        print(color_text("❌ Unable to parse blockchain data format", COLORS['R']))
        return None

    def _process_block_list(self, block_list):
        """Process a list of block data - return as-is for later conversion"""
        if not isinstance(block_list, list):
            return None
            
        loaded_chain = []
        for i, block_data in enumerate(block_list):
            try:
                if isinstance(block_data, (dict, Block)):
                    loaded_chain.append(block_data)
                else:
                    print(color_text(f"⚠️  Invalid block type at index {i}: {type(block_data)}", COLORS['O']))
            except Exception as e:
                print(color_text(f"⚠️  Error loading block {i}: {e}", COLORS['O']))
                continue
        
        if loaded_chain:
            print(color_text(f"✅ Loaded {len(loaded_chain)} blocks from storage", COLORS['G']))
            return loaded_chain
        
        return None

    def get_transaction_signature(self, transaction):
        """Create a unique signature for any transaction type"""
        if transaction.get('signature'):
            return transaction['signature']
        
        if transaction.get('serial_number'):
            return f"serial_{transaction['serial_number']}"
        
        if transaction.get('front_serial'):
            return f"front_{transaction['front_serial']}"
        
        # Fallback: create hash of transaction content
        tx_content = json.dumps(transaction, sort_keys=True)
        return hashlib.sha256(tx_content.encode()).hexdigest()[:32]

    def _get_block_info(self, block):
        """Safely extract info from block whether it's a Block object or dict"""
        if isinstance(block, Block):
            return {
                'index': block.index,
                'hash': block.hash,
                'transactions': block.transactions
            }
        elif isinstance(block, dict):
            return {
                'index': block.get('index', 0),
                'hash': block.get('hash', 'unknown'),
                'transactions': block.get('transactions', [])
            }
        else:
            # Handle unexpected types by creating a default block info
            print(color_text(f"⚠️  Unexpected block type: {type(block)}", COLORS['O']))
            return {
                'index': 0,
                'hash': 'unknown',
                'transactions': []
            }

    def find_unmined_transactions(self):
        """Find bill transactions that haven't been rewarded yet"""
        unmined_transactions = []
        
        if not isinstance(self.chain, list):
            print(color_text("❌ Blockchain is not a valid list", COLORS['R']))
            return unmined_transactions
        
        for block in self.chain:
            try:
                block_info = self._get_block_info(block)
                transactions = block_info['transactions']
                
                if not isinstance(transactions, list):
                    continue
                    
                for tx in transactions:
                    if not isinstance(tx, dict):
                        continue
                        
                    # Skip reward and genesis transactions
                    if tx.get('type') in ['reward', 'genesis', 'bulk_reward']:
                        continue
                    
                    # Look for bill transactions (have serial numbers)
                    if tx.get('serial_number') or tx.get('front_serial'):
                        tx_signature = self.get_transaction_signature(tx)
                        
                        if not self.config.is_transaction_mined(tx_signature):
                            unmined_transactions.append({
                                'transaction': tx,
                                'block_index': block_info['index'],
                                'block_hash': block_info['hash'],
                                'signature': tx_signature
                            })
            except Exception as e:
                print(color_text(f"⚠️ Error processing block: {e}", COLORS['O']))
                continue
        
        return unmined_transactions

    def save_chain(self):
        """Save blockchain to local storage - convert all to dicts"""
        chain_data = []
        for block in self.chain:
            if isinstance(block, Block):
                chain_data.append(block.to_dict())
            elif isinstance(block, dict):
                chain_data.append(block)
            else:
                print(color_text(f"⚠️  Skipping invalid block type: {type(block)}", COLORS['O']))
        
        ConfigManager.save_json(self.chain_file, chain_data)

    def auto_sync(self):
        """Auto-sync blockchain and mempool on startup"""
        time.sleep(2)
        print(color_text("🔄 Auto-syncing blockchain and mempool...", COLORS['B']))
        
        # Sync blockchain
        if self.sync_from_web():
            print(color_text("✅ Web sync completed", COLORS['G']))
        elif self.sync_from_peers():
            print(color_text("✅ Peer sync completed", COLORS['G']))
        else:
            print(color_text("⚠️  Blockchain sync failed, using local chain", COLORS['O']))
        
        # Sync mempool
        if self.sync_mempool_from_api():
            print(color_text("✅ Mempool sync completed", COLORS['G']))
        else:
            print(color_text("⚠️  Mempool sync failed, using local mempool", COLORS['O']))

    def sync_mempool_from_api(self):
        """Sync mempool from the API endpoint"""
        try:
            print(color_text("🌐 Syncing mempool from bank.linglin.art...", COLORS['I']))
            response = requests.get(f"{self.config.api_base_url}/mempool", timeout=30)
            
            if response.status_code == 200:
                api_mempool = response.json()
                
                if isinstance(api_mempool, list):
                    print(color_text(f"📥 Downloaded {len(api_mempool)} transactions from API mempool", COLORS['G']))
                    
                    # Merge with local mempool
                    merged_mempool = self.merge_mempools(self.mempool, api_mempool)
                    new_transactions = len(merged_mempool) - len(self.mempool)
                    
                    if new_transactions > 0:
                        print(color_text(f"🔄 Added {new_transactions} new transactions to mempool", COLORS['G']))
                        self.mempool = merged_mempool
                        self.save_mempool()
                        self.config.last_mempool_sync = time.time()
                        self.config.save_config()
                        return True
                    else:
                        print(color_text("ℹ️  Mempool is already up to date", COLORS['B']))
                        return True
                else:
                    print(color_text("❌ Invalid mempool format from API", COLORS['R']))
            else:
                print(color_text(f"❌ API returned status code: {response.status_code}", COLORS['R']))
                
        except requests.exceptions.RequestException as e:
            print(color_text(f"❌ Network error during mempool sync: {e}", COLORS['R']))
        except Exception as e:
            print(color_text(f"❌ Error during mempool sync: {e}", COLORS['R']))
        
        return False

    def merge_mempools(self, local_mempool, api_mempool):
        """Merge local and API mempools, removing duplicates"""
        print(color_text("🔄 Merging mempools...", COLORS['B']))
        
        # Create a set of transaction signatures for quick lookup
        local_signatures = set()
        for tx in local_mempool:
            signature = self.get_transaction_signature(tx)
            local_signatures.add(signature)
        
        # Add transactions from API that aren't in local mempool
        merged_mempool = local_mempool.copy()
        added_count = 0
        
        for api_tx in api_mempool:
            api_signature = self.get_transaction_signature(api_tx)
            if api_signature not in local_signatures:
                merged_mempool.append(api_tx)
                added_count += 1
                local_signatures.add(api_signature)  # Add to set to avoid duplicates in this loop
        
        print(color_text(f"📊 Mempool merge: {len(local_mempool)} local + {added_count} new = {len(merged_mempool)} total", COLORS['G']))
        return merged_mempool

    def sync_from_web(self):
        """Sync blockchain from your web API"""
        try:
            print(color_text("🌐 Syncing from bank.linglin.art...", COLORS['I']))
            response = requests.get(f"{self.config.api_base_url}/blockchain", timeout=30)
            
            if response.status_code == 200:
                remote_chain_data = response.json()
                
                if isinstance(remote_chain_data, list):
                    # Convert all remote blocks to Block objects
                    remote_chain = []
                    for block_dict in remote_chain_data:
                        if isinstance(block_dict, dict):
                            try:
                                block = Block.from_dict(block_dict)
                                remote_chain.append(block)
                            except Exception as e:
                                print(color_text(f"⚠️  Error converting block: {e}", COLORS['O']))
                                continue
                    
                    if remote_chain and len(remote_chain) > len(self.chain):
                        print(color_text(f"🔄 Downloading {len(remote_chain) - len(self.chain)} new blocks", COLORS['G']))
                        self.chain = remote_chain
                        self.save_chain()
                        self.config.last_sync = time.time()
                        self.config.save_config()
                        return True
                    elif remote_chain and len(remote_chain) <= len(self.chain):
                        print(color_text("ℹ️  Local chain is up to date", COLORS['B']))
                        return True
                else:
                    print(color_text("❌ Invalid response format from API", COLORS['R']))
            else:
                print(color_text(f"❌ API returned status code: {response.status_code}", COLORS['R']))
                
        except requests.exceptions.RequestException as e:
            print(color_text(f"❌ Network error during web sync: {e}", COLORS['R']))
        except Exception as e:
            print(color_text(f"❌ Error during web sync: {e}", COLORS['R']))
        
        return False

    def get_mempool(self):
        """Get current mempool (local + merged)"""
        return self.mempool

    def get_blockchain_status(self):
        """Get blockchain status from API"""
        try:
            response = requests.get(f"{self.config.api_base_url}/api/blockchain/status", timeout=10)
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            print(color_text(f"❌ Error fetching blockchain status: {e}", COLORS['R']))
            return {}

    def broadcast_transaction(self, transaction):
        """Broadcast a transaction to the network"""
        try:
            response = requests.post(
                f"{self.config.api_base_url}/api/transaction/broadcast",
                json=transaction,
                timeout=10
            )
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    return True
            return False
        except Exception as e:
            print(color_text(f"❌ Error broadcasting transaction: {e}", COLORS['R']))
            return False

    def mine_block_via_api(self):
        """Mine a block using the API endpoint"""
        try:
            response = requests.post(
                f"{self.config.api_base_url}/api/block/mine",
                json={"miner_address": self.config.miner_address},
                timeout=30
            )
        except:
            print("Invalid API request!")
            return
        return response

    def get_block_details(self, block_hash):
        """Get detailed block information from API"""
        try:
            response = requests.get(f"{self.config.api_base_url}/api/block/{block_hash}", timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    return result
            return None
        except Exception as e:
            print(color_text(f"❌ Error fetching block details: {e}", COLORS['R']))
            return None

    def sync_from_peers(self):
        """Try to sync from known peers (placeholder)"""
        known_peers = ConfigManager.load_json("peers.json", [])
        for peer in known_peers:
            try:
                print(color_text(f"🔗 Trying peer: {peer}", COLORS['B']))
                time.sleep(0.5)
            except:
                continue
        return False

    def _ensure_valid_chain_structure(self):
        """Ensure self.chain is a proper list and fix if needed"""
        # If chain is not a list, initialize it
        if not isinstance(self.chain, list):
            print(color_text("⚠️  Blockchain is not a list, initializing new chain", COLORS['O']))
            self.chain = [self.create_genesis_block()]
            return
        
        # If chain is empty, add genesis block
        if len(self.chain) == 0:
            print(color_text("⚠️  Blockchain is empty, adding genesis block", COLORS['O']))
            self.chain = [self.create_genesis_block()]
            return
        
        # If chain is actually a dictionary (common issue), convert it
        if isinstance(self.chain, dict):
            print(color_text("⚠️  Chain is a dictionary, converting to list", COLORS['O']))
            new_chain = []
            
            # Try to extract blocks from dictionary
            for key, value in self.chain.items():
                if isinstance(value, (dict, Block)):
                    # Try to determine if this is a block
                    if isinstance(value, dict) and ('index' in value or 'transactions' in value or 'hash' in value):
                        try:
                            block = Block.from_dict(value)
                            new_chain.append(block)
                        except Exception as e:
                            print(color_text(f"⚠️  Could not convert dict to block: {e}", COLORS['O']))
                    else:
                        new_chain.append(value)
            
            # If we didn't find any blocks, start fresh
            if not new_chain:
                print(color_text("⚠️  No valid blocks found in dictionary, creating new chain", COLORS['O']))
                new_chain = [self.create_genesis_block()]
            
            self.chain = new_chain
            self.save_chain()

    def add_transaction(self, transaction_data):
        """Create and broadcast a transaction to all network nodes and API endpoints"""
    
        try:
            # Create transaction
            transaction = self.create_transaction_structure(transaction_data)
            print(color_text(f"📋 Created transaction: {transaction['hash']}", COLORS['B']))
            
            # Get all broadcast targets
            broadcast_targets = self.get_broadcast_targets()
            print(color_text(f"🌐 Broadcasting to {len(broadcast_targets)} targets", COLORS['B']))
            
            # Broadcast to all targets
            success_count = self.broadcast_to_targets(transaction, broadcast_targets)
            
            if success_count > 0:
                print(color_text(f"✅ Successfully broadcasted to {success_count}/{len(broadcast_targets)} targets", COLORS['G']))
                return True
            else:
                print(color_text(f"❌ Failed to broadcast to any targets", COLORS['R']))
                return False
            
        except Exception as e:
            print(color_text(f"❌ Transaction failed: {str(e)}", COLORS['R']))
            return False

    def get_broadcast_targets(self):
        """Get all RPC nodes and API endpoints to broadcast to"""
        targets = []
        
        # Add RPC nodes
        targets.extend(self.known_nodes)
        
        # Add API endpoints
        api_endpoints = [
            "https://bank.linglin.art/api/transaction/broadcast"
        ]
        
        # Add base_url endpoint if available
        if hasattr(self, 'base_url') and self.base_url:
            api_endpoints.append(f"{self.base_url.rstrip('/')}/api/transaction/broadcast")
        
        targets.extend(api_endpoints)
        
        # Remove duplicates and return
        return list(set(targets))
    def broadcast_reward_transaction(self, reward_data):
        """Broadcast a reward transaction to the API"""
        try:
            print(color_text("🌐 Broadcasting reward transaction to API...", COLORS['B']))
            
            # Structure the reward transaction according to the API format
            reward_tx = {
                "to": reward_data.get("to", ""),
                "amount": float(reward_data.get("amount", 0)),  # Ensure it's a float
                "description": reward_data.get("description", "Mining reward"),
                "block_height": int(reward_data.get("block_height", 0)),  # Ensure it's an int
                "type": "reward"
            }
            
            # Validate required fields
            if not reward_tx["to"]:
                print(color_text("❌ Cannot broadcast reward: missing 'to' address", COLORS['R']))
                return False
            
            if reward_tx["amount"] <= 0:
                print(color_text("❌ Cannot broadcast reward: invalid amount", COLORS['R']))
                return False
            
            response = requests.post(
                f"{self.config.api_base_url}/api/transaction/reward",
                json=reward_tx,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    print(color_text(f"✅ Reward transaction broadcasted successfully!", COLORS['G']))
                    print(color_text(f"📝 Transaction hash: {result.get('transaction_hash', 'unknown')}", COLORS['B']))
                    return True
                else:
                    print(color_text(f"❌ API returned error: {result.get('message', 'Unknown error')}", COLORS['R']))
            else:
                print(color_text(f"❌ API returned status code: {response.status_code}", COLORS['R']))
                print(color_text(f"📋 Response: {response.text}", COLORS['O']))
                
        except Exception as e:
            print(color_text(f"❌ Error broadcasting reward transaction: {e}", COLORS['R']))
        
        return False
    def create_transaction_structure(self, transaction_data):
        """Create properly structured transaction"""
        transaction = {
            "type": "transaction",
            "timestamp": time.time(),
            "data": transaction_data,
            "signature": transaction_data.get('signature')
        }
        
        transaction_hash = self.calculate_hash(transaction)
        transaction["hash"] = transaction_hash
        
        return transaction

    def broadcast_to_targets(self, transaction, targets):
        """Broadcast transaction to multiple targets"""
        success_count = 0
        
        for target in targets:
            url = self.format_broadcast_url(target)
            
            try:
                response = requests.post(url, json=transaction, timeout=10)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("status") == "success":
                        print(color_text(f"✅ Accepted by {self.get_target_name(target)}", COLORS['G']))
                        success_count += 1
                    else:
                        print(color_text(f"❌ {self.get_target_name(target)} rejected: {result.get('message')}", COLORS['R']))
                else:
                    print(color_text(f"⚠️  {self.get_target_name(target)} returned {response.status_code}", COLORS['O']))
                    
            except requests.exceptions.RequestException as e:
                print(color_text(f"❌ Failed to reach {self.get_target_name(target)}: {str(e)}", COLORS['R']))
            except Exception as e:
                print(color_text(f"❌ Error broadcasting to {self.get_target_name(target)}: {str(e)}", COLORS['R']))
        
        return success_count

    def format_broadcast_url(self, target):
        """Format the broadcast URL based on target type"""
        if target.startswith("http"):
            return target
        else:
            return f"http://{target}/api/transaction/broadcast"

    def get_target_name(self, target):
        """Get display name for broadcast target"""
        if target.startswith("http"):
            return target.split("//")[-1].split("/")[0]
        else:
            return target

    def calculate_hash(self, data):
        """Calculate SHA256 hash of data"""
        data_string = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_string.encode()).hexdigest()

    def get_latest_block(self):
        """Get the latest block in the chain"""
        if not self.chain:
            return None
        return self.chain[-1]

    def get_chain_length(self):
        """Get the length of the blockchain"""
        return len(self.chain)

    def is_chain_valid(self):
        """Validate the entire blockchain"""
        if not self.chain:
            return False
        
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]
            
            # Check if current block hash is valid
            if current_block.hash != current_block.calculate_hash():
                return False
            
            # Check if previous block hash matches
            if current_block.previous_hash != previous_block.hash:
                return False
        
        return True

class LunaNode:
    def __init__(self):
        self.config = NodeConfig()
        self.blockchain = Blockchain(self.config)
        self.running = True
        self.mining_thread = None
        self.auto_mine_thread = None
        
        # Ensure we have a miner address
        if not self.config.miner_address:
            self.config.miner_address = self.config.generate_miner_address()
            self.config.save_config()
        
        # Register cleanup
        atexit.register(self.cleanup)
        
        print(color_text(f"\n🌙 {COLORS['BOLD']}Luna Node v{self.config.node_version}{COLORS['X']}", COLORS['I']))
        print(color_text(f"🆔 Node ID: {self.config.node_id}", COLORS['B']))
        print(color_text(f"⛏️  Miner: {self.config.miner_address}", COLORS['G']))
        print(color_text(f"🔗 Chain Length: {self.blockchain.get_chain_length()}", COLORS['Y']))
        print(color_text(f"📊 Mempool Size: {len(self.blockchain.mempool)}", COLORS['O']))
        print(color_text(f"🎯 Difficulty: {self.config.difficulty}", COLORS['R']))
        print("=" * 60)
        
        # Start auto-mining if enabled
        if self.config.auto_mine:
            self.start_auto_mining()

    def cleanup(self):
        """Cleanup resources on exit"""
        self.running = False
        if self.mining_thread and self.mining_thread.is_alive():
            self.mining_thread.join(timeout=1)
        if self.auto_mine_thread and self.auto_mine_thread.is_alive():
            self.auto_mine_thread.join(timeout=1)

    def start_auto_mining(self):
        """Start auto-mining in background thread"""
        if self.auto_mine_thread and self.auto_mine_thread.is_alive():
            return
        
        self.auto_mine_thread = threading.Thread(target=self._auto_mine_worker, daemon=True)
        self.auto_mine_thread.start()
        print(color_text("🤖 Auto-mining started!", COLORS['G']))
    def _mine_pending_transactions_local(self, miner_address):
        """Local mining fallback - mines both mempool bills and pending transactions"""
        try:
            # Get transactions from both sources
            available_bills = []
            pending_transfers = []
            
            # 1. Check mempool for bill transactions
            if hasattr(self, 'mempool') and self.mempool:
                for tx in self.mempool:
                    if tx.get("type") in ["GTX_Genesis", "genesis"]:
                        serial = tx.get("serial_number")
                        if serial and not self._is_transaction_mined(serial):
                            available_bills.append(tx)
            
            # 2. Check pending_transactions for regular transfers
            if hasattr(self, 'pending_transactions') and self.pending_transactions:
                for tx in self.pending_transactions:
                    # Skip if already mined (check by signature/hash)
                    if not self._is_transfer_mined(tx):
                        pending_transfers.append(tx)
            
            # Combine all transactions to mine
            all_transactions = available_bills + pending_transfers
            
            if not all_transactions:
                print(color_text("⏭️ No transactions available to mine", COLORS['O']))
                return None

            print(color_text(f"⛏️ Mining block with {len(all_transactions)} transactions:", COLORS['B']))
            print(color_text(f"   - {len(available_bills)} bill(s)", COLORS['B']))
            print(color_text(f"   - {len(pending_transfers)} transfer(s)", COLORS['B']))
            
            # Create reward transaction (base reward + bonus per transaction)
            base_reward = self.config.mining_reward
            bonus_reward = 10  # Additional reward per transaction
            total_reward = base_reward + (bonus_reward * len(all_transactions))
            
            reward_tx = {
                "type": "reward",
                "to": miner_address,
                "amount": total_reward,
                "timestamp": time.time(),
                "signature": f"reward_{int(time.time())}",
                "miner": miner_address,
                "description": f"Mining reward for {len(all_transactions)} transactions ({len(available_bills)} bills + {len(pending_transfers)} transfers)"
            }

            # All transactions for this block
            block_transactions = all_transactions + [reward_tx]
            
            # Get previous hash
            previous_hash = "0"
            if hasattr(self, 'blockchain') and self.blockchain:
                last_block = self.blockchain[-1]
                previous_hash = last_block.get("hash", "0")
            elif hasattr(self, 'chain') and self.chain:
                last_block = self.chain[-1]
                if hasattr(last_block, 'hash'):
                    previous_hash = last_block.hash
                else:
                    previous_hash = last_block.get("hash", "0")
            
            # Create new block
            new_block = {
                "index": len(self.blockchain) if hasattr(self, 'blockchain') else len(self.chain),
                "timestamp": time.time(),
                "transactions": block_transactions,
                "previous_hash": previous_hash,
                "nonce": 0,
                "miner": miner_address,
                "difficulty": self.config.difficulty,
                "hash": ""  # Will be calculated during mining
            }
            
            # Mine the block (simple proof of work)
            self.is_mining = True
            new_block = self._mine_block(new_block, self.config.difficulty)
            self.is_mining = False
            
            # Add to chain
            if hasattr(self, 'blockchain'):
                self.blockchain.append(new_block)
            else:
                self.chain.append(new_block)
            
            # Remove mined transactions from both sources
            self._remove_mined_transactions(available_bills, pending_transfers)
            
            # Save data
            self._save_blockchain()
            self._save_mempool()
            self._save_pending_transactions()
            
            # Create verification URL
            verification_url = f"{self.config.api_base_url}/block/{new_block['hash']}"
            
            print(color_text(f"💰 Block #{new_block['index']} mined! Reward: {total_reward} LKC", COLORS['G']))
            print(color_text(f"📦 Transactions: {len(available_bills)} bills + {len(pending_transfers)} transfers", COLORS['G']))
            print(color_text(f"📄 Verification: {verification_url}", COLORS['B']))
            
            return new_block
            
        except Exception as e:
            print(color_text(f"❌ Error mining block: {e}", COLORS['R']))
            import traceback
            traceback.print_exc()
            self.is_mining = False
            return None

    def _is_transfer_mined(self, transaction):
        """Check if a transfer transaction has already been mined"""
        chain = self.blockchain if hasattr(self, 'blockchain') else self.chain
        
        # Use signature or hash to identify the transaction
        tx_id = transaction.get("signature") or transaction.get("hash")
        if not tx_id:
            return False
            
        for block in chain:
            for tx in block.get("transactions", []):
                if tx.get("signature") == tx_id or tx.get("hash") == tx_id:
                    return True
        return False

    def _remove_mined_transactions(self, mined_bills, mined_transfers):
        """Remove mined transactions from both mempool and pending_transactions"""
        # Remove from mempool (bills)
        if hasattr(self, 'mempool') and mined_bills:
            mined_serials = {tx.get("serial_number") for tx in mined_bills if tx.get("serial_number")}
            self.mempool = [tx for tx in self.mempool if tx.get("serial_number") not in mined_serials]
        
        # Remove from pending_transactions (transfers)
        if hasattr(self, 'pending_transactions') and mined_transfers:
            mined_signatures = {tx.get("signature") for tx in mined_transfers if tx.get("signature")}
            mined_hashes = {tx.get("hash") for tx in mined_transfers if tx.get("hash")}
            
            self.pending_transactions = [
                tx for tx in self.pending_transactions 
                if tx.get("signature") not in mined_signatures and tx.get("hash") not in mined_hashes
            ]

    def _save_pending_transactions(self):
        """Save pending transactions to file"""
        try:
            if hasattr(self, 'pending_transactions'):
                with open("pending_transactions.json", "w") as f:
                    json.dump(self.pending_transactions, f, indent=2)
        except Exception as e:
            print(f"Error saving pending transactions: {e}")
    def stop_auto_mining(self):
        """Stop auto-mining"""
        self.config.auto_mine = False
        self.config.save_config()
        print(color_text("⏹️  Auto-mining stopped", COLORS['O']))

    def _auto_mine_worker(self):
        """Background worker for auto-mining"""
        while self.running and self.config.auto_mine:
            try:
                # Check for unmined transactions
                unmined_txs = self.blockchain.find_unmined_transactions()
                if unmined_txs:
                    print(color_text(f"🤖 Auto-mining {len(unmined_txs)} unmined transactions...", COLORS['G']))
                    self.mine_block()
                else:
                    # Check mempool for transactions
                    if self.blockchain.mempool:
                        print(color_text(f"🤖 Auto-mining {len(self.blockchain.mempool)} mempool transactions...", COLORS['G']))
                        self.mine_block()
                
                # Wait before next check
                time.sleep(30)
            except Exception as e:
                print(color_text(f"🤖 Auto-mining error: {e}", COLORS['R']))
                time.sleep(60)
    def mine_from_mempool(self):
        """Mine a block using transactions from the mempool"""
        if self.blockchain.is_mining:
            print(color_text("⚠️  Mining already in progress", COLORS['O']))
            return False
        
        self.blockchain.is_mining = True
        try:
            # Get current mempool
            mempool = self.blockchain.get_mempool()
            
            if not mempool:
                print(color_text("📭 Mempool is empty", COLORS['O']))
                return False
            
            print(color_text(f"📊 Mempool has {len(mempool)} transactions", COLORS['B']))
            
            # Filter out transactions that have already been mined
            unmined_txs = []
            for tx in mempool:
                tx_signature = self.blockchain.get_transaction_signature(tx)
                if not self.config.is_transaction_mined(tx_signature):
                    unmined_txs.append(tx)
                else:
                    print(color_text(f"⏭️  Skipping already mined transaction: {tx_signature[:16]}...", COLORS['O']))
            
            if not unmined_txs:
                print(color_text("ℹ️  No unmined transactions in mempool", COLORS['B']))
                return False
            
            print(color_text(f"⛏️  Preparing to mine {len(unmined_txs)} unmined transactions from mempool", COLORS['G']))
            
            # Show transaction types
            tx_types = {}
            for tx in unmined_txs:
                tx_type = tx.get('type', 'unknown')
                tx_types[tx_type] = tx_types.get(tx_type, 0) + 1
            
            for tx_type, count in tx_types.items():
                print(color_text(f"   - {count} {tx_type} transactions", COLORS['Y']))
            
            # Create new block
            latest_block = self.blockchain.get_latest_block()
            if latest_block is None:
                print(color_text("❌ Cannot get latest block", COLORS['R']))
                return False
            
            new_index = latest_block.index + 1 if hasattr(latest_block, 'index') else len(self.blockchain.chain)
            previous_hash = latest_block.hash if hasattr(latest_block, 'hash') else "0"
            
            # Add mining reward transaction
            base_reward = self.config.mining_reward
            bonus_per_tx = 0.1  # Bonus for each transaction mined
            total_reward = base_reward + (bonus_per_tx * len(unmined_txs))
            
            reward_tx = {
                "type": "reward",
                "miner": self.config.miner_address,
                "amount": total_reward,
                "timestamp": time.time(),
                "transactions_mined": len(unmined_txs),
                "description": f"Mining reward for {len(unmined_txs)} mempool transactions"
            }
            
            # Combine transactions
            transactions = unmined_txs + [reward_tx]
            
            # Create and mine block
            new_block = Block(new_index, previous_hash, transactions)
            
            def mining_progress(hashes_tried, hash_rate, progress):
                if hashes_tried % 1000 == 0:
                    hash_rate_str = f"{hash_rate/1000:.1f} kH/s" if hash_rate > 1000 else f"{hash_rate:.1f} H/s"
                    print(f"⛏️  Mining... {hashes_tried:,} hashes | {hash_rate_str} | {progress:.1%}")
            
            print(color_text(f"🎯 Starting to mine block #{new_index} with difficulty {self.config.difficulty}", COLORS['B']))
            
            if new_block.mine_block(self.config.difficulty, mining_progress):
                # Add block to chain
                self.blockchain.chain.append(new_block)
                self.blockchain.save_chain()
                
                # Mark transactions as mined
                for tx in unmined_txs:
                    tx_signature = self.blockchain.get_transaction_signature(tx)
                    self.config.mark_transaction_mined(tx_signature, new_block.hash)
                
                # BROADCAST REWARD TO API
                reward_data = {
                    "to": self.config.miner_address,
                    "amount": total_reward,
                    "description": f"Mined block #{new_index} with {len(unmined_txs)} transactions",
                    "block_height": new_index
                }
                
                # Broadcast reward to API
                if self.blockchain.broadcast_reward_transaction(reward_data):
                    print(color_text("💰 Reward successfully submitted to network!", COLORS['G']))
                else:
                    print(color_text("⚠️  Reward submission failed, but block was mined locally", COLORS['O']))
                
                # Remove mined transactions from mempool
                self._remove_mined_from_mempool(unmined_txs)
                
                # Add to mining history
                self.config.add_bill(
                    new_block.hash,
                    total_reward,
                    time.time(),
                    f"{self.config.api_base_url}/block/{new_block.hash}",
                    len(unmined_txs)
                )
                
                print(color_text(f"✅ Block #{new_index} mined successfully from mempool!", COLORS['G']))
                print(color_text(f"💰 Reward: {total_reward} LUN", COLORS['Y']))
                print(color_text(f"📊 Transactions: {len(unmined_txs)}", COLORS['B']))
                print(color_text(f"⏱️  Time: {new_block.mining_time:.2f}s", COLORS['I']))
                print(color_text(f"📝 Block Hash: {new_block.hash}", COLORS['V']))
                
                return True
            else:
                print(color_text("❌ Mining failed", COLORS['R']))
                return False
                
        except Exception as e:
            print(color_text(f"❌ Error mining from mempool: {e}", COLORS['R']))
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.blockchain.is_mining = False

    def _remove_mined_from_mempool(self, mined_transactions):
        """Remove mined transactions from mempool"""
        try:
            current_mempool = self.blockchain.get_mempool()
            if not current_mempool:
                return
            
            # Create set of signatures for quick lookup
            mined_signatures = {self.blockchain.get_transaction_signature(tx) for tx in mined_transactions}
            
            # Filter out mined transactions
            new_mempool = [
                tx for tx in current_mempool 
                if self.blockchain.get_transaction_signature(tx) not in mined_signatures
            ]
            
            removed_count = len(current_mempool) - len(new_mempool)
            
            if removed_count > 0:
                self.blockchain.update_mempool(new_mempool)
                print(color_text(f"🗑️  Removed {removed_count} mined transactions from mempool", COLORS['G']))
            else:
                print(color_text("ℹ️  No transactions to remove from mempool", COLORS['B']))
                
        except Exception as e:
            print(color_text(f"❌ Error removing transactions from mempool: {e}", COLORS['R']))
    def mine_block(self):
        """Mine a new block with unmined transactions"""
        if self.blockchain.is_mining:
            print(color_text("⚠️  Mining already in progress", COLORS['O']))
            return False
        
        self.blockchain.is_mining = True
        try:
            # Get unmined transactions
            unmined_txs = self.blockchain.find_unmined_transactions()
            
            if not unmined_txs:
                print(color_text("ℹ️  No unmined transactions found", COLORS['B']))
                return False
            
            print(color_text(f"⛏️  Found {len(unmined_txs)} unmined transactions", COLORS['G']))
            
            # Create new block
            latest_block = self.blockchain.get_latest_block()
            if latest_block is None:
                print(color_text("❌ Cannot get latest block", COLORS['R']))
                return False
            
            new_index = latest_block.index + 1 if hasattr(latest_block, 'index') else len(self.blockchain.chain)
            previous_hash = latest_block.hash if hasattr(latest_block, 'hash') else "0"
            
            # Extract transaction data
            transactions = [tx['transaction'] for tx in unmined_txs]
            
            # Add mining reward transaction
            reward_tx = {
                "type": "reward",
                "miner": self.config.miner_address,
                "amount": self.config.mining_reward + len(transactions) * 0.1,  # Base + transaction fees
                "timestamp": time.time(),
                "transactions_mined": len(transactions)
            }
            transactions.append(reward_tx)
            
            # Create and mine block
            new_block = Block(new_index, previous_hash, transactions)
            
            def mining_progress(hashes_tried, hash_rate, progress):
                if hashes_tried % 1000 == 0:
                    print(f"⛏️  Mining... {hashes_tried:,} hashes | {hash_rate:.1f} H/s | {progress:.1%}")
            
            if new_block.mine_block(self.config.difficulty, mining_progress):
                # Add block to chain
                self.blockchain.chain.append(new_block)
                self.blockchain.save_chain()
                
                # Mark transactions as mined
                for tx_info in unmined_txs:
                    self.config.mark_transaction_mined(tx_info['signature'], new_block.hash)
                
                # Add to mining history
                total_reward = self.config.mining_reward + len(unmined_txs) * 0.1
                self.config.add_bill(
                    new_block.hash,
                    total_reward,
                    time.time(),
                    f"Mined block #{new_index}",
                    len(unmined_txs)
                )
                
                print(color_text(f"✅ Block #{new_index} mined successfully!", COLORS['G']))
                print(color_text(f"💰 Reward: {total_reward} LUN", COLORS['Y']))
                print(color_text(f"📊 Transactions: {len(unmined_txs)}", COLORS['B']))
                print(color_text(f"⏱️  Time: {new_block.mining_time:.2f}s", COLORS['I']))
                
                return True
            else:
                print(color_text("❌ Mining failed", COLORS['R']))
                return False
                
        except Exception as e:
            print(color_text(f"❌ Mining error: {e}", COLORS['R']))
            return False
        finally:
            self.blockchain.is_mining = False

    def sync_mempool(self):
        """Manually sync mempool from API"""
        print(color_text("🔄 Manually syncing mempool...", COLORS['B']))
        if self.blockchain.sync_mempool_from_api():
            print(color_text("✅ Mempool sync completed", COLORS['G']))
        else:
            print(color_text("❌ Mempool sync failed", COLORS['R']))

    def show_status(self):
        """Display node status"""
        print(color_text(f"\n📊 {COLORS['BOLD']}Node Status{COLORS['X']}", COLORS['B']))
        print("=" * 40)
        print(color_text(f"🆔 Node ID: {self.config.node_id[:16]}...", COLORS['B']))
        print(color_text(f"⛏️  Miner: {self.config.miner_address}", COLORS['G']))
        print(color_text(f"🔗 Chain Length: {self.blockchain.get_chain_length()}", COLORS['Y']))
        print(color_text(f"📊 Mempool Size: {len(self.blockchain.mempool)}", COLORS['O']))
        print(color_text(f"🎯 Difficulty: {self.config.difficulty}", COLORS['R']))
        print(color_text(f"💰 Mining Reward: {self.config.mining_reward} LUN", COLORS['I']))
        print(color_text(f"🤖 Auto-mine: {'Enabled' if self.config.auto_mine else 'Disabled'}", COLORS['V']))
        
        # Mining history
        total_bills, total_reward, total_txs = self.config.get_bills_summary()
        print(color_text(f"📈 Bills Mined: {total_bills}", COLORS['G']))
        print(color_text(f"💰 Total Reward: {total_reward} LUN", COLORS['Y']))
        print(color_text(f"📊 Total Transactions: {total_txs}", COLORS['B']))
        
        # Last sync
        if self.config.last_sync > 0:
            last_sync_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.config.last_sync))
            print(color_text(f"🔄 Last Sync: {last_sync_time}", COLORS['I']))
        
        if self.config.last_mempool_sync > 0:
            last_mempool_sync = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.config.last_mempool_sync))
            print(color_text(f"📥 Last Mempool Sync: {last_mempool_sync}", COLORS['V']))

    def show_menu(self):
        """Display main menu"""
        while self.running:
            print(color_text(f"\n🌙 {COLORS['BOLD']}Luna Node Menu{COLORS['X']}", COLORS['I']))
            print("=" * 50)
            print(color_text("1. 📊 Show Status", COLORS['B']))
            print(color_text("2. ⛏️  Mine Block", COLORS['G']))
            print(color_text("3. 🔄 Sync Blockchain", COLORS['Y']))
            print(color_text("4. 📥 Sync Mempool", COLORS['O']))
            print(color_text("5. ⚙️  Settings", COLORS['R']))
            print(color_text("6. 📈 Mining History", COLORS['I']))
            print(color_text("7. 🤖 Auto-mine Toggle", COLORS['V']))
            print(color_text("8. 🚪 Exit", COLORS['X']))
            
            try:
                choice = input(color_text("\n🎯 Enter your choice (1-8): ", COLORS['BOLD'])).strip()
                
                if choice == "1":
                    self.show_status()
                elif choice == "2":
                    self.mine_from_mempool()
                    self.mine_block()
                elif choice == "3":
                    if self.blockchain.sync_from_web():
                        print(color_text("✅ Blockchain sync completed", COLORS['G']))
                    else:
                        print(color_text("❌ Blockchain sync failed", COLORS['R']))
                elif choice == "4":
                    self.sync_mempool()
                elif choice == "5":
                    self.settings_menu()
                elif choice == "6":
                    self.show_mining_history()
                elif choice == "7":
                    self.toggle_auto_mine()
                elif choice == "8":
                    print(color_text("👋 Goodbye!", COLORS['G']))
                    self.running = False
                else:
                    print(color_text("❌ Invalid choice", COLORS['R']))
                    
            except KeyboardInterrupt:
                print(color_text("\n👋 Goodbye!", COLORS['G']))
                self.running = False
            except Exception as e:
                print(color_text(f"❌ Error: {e}", COLORS['R']))

    def toggle_auto_mine(self):
        """Toggle auto-mining on/off"""
        self.config.auto_mine = not self.config.auto_mine
        self.config.save_config()
        
        if self.config.auto_mine:
            print(color_text("✅ Auto-mining enabled", COLORS['G']))
            self.start_auto_mining()
        else:
            print(color_text("⏹️  Auto-mining disabled", COLORS['O']))
            self.stop_auto_mining()

    def settings_menu(self):
        """Display settings menu"""
        while True:
            print(color_text(f"\n⚙️ {COLORS['BOLD']}Settings{COLORS['X']}", COLORS['R']))
            print("=" * 40)
            print(color_text(f"1. 🎯 Difficulty: {self.config.difficulty}", COLORS['B']))
            print(color_text(f"2. 💰 Mining Reward: {self.config.mining_reward} LUN", COLORS['G']))
            print(color_text(f"3. ⛏️  Miner Address: {self.config.miner_address}", COLORS['Y']))
            print(color_text("4. ↩️  Back to Main Menu", COLORS['O']))
            
            try:
                choice = input(color_text("\n🎯 Enter your choice (1-4): ", COLORS['BOLD'])).strip()
                
                if choice == "1":
                    new_diff = input(f"Enter new difficulty (1-8, current: {self.config.difficulty}): ").strip()
                    try:
                        new_diff = int(new_diff)
                        if self.config.update_difficulty(new_diff):
                            print(color_text(f"✅ Difficulty updated to {new_diff}", COLORS['G']))
                        else:
                            print(color_text("❌ Invalid difficulty (must be 1-8)", COLORS['R']))
                    except ValueError:
                        print(color_text("❌ Please enter a valid number", COLORS['R']))
                        
                elif choice == "2":
                    new_reward = input(f"Enter new mining reward (current: {self.config.mining_reward}): ").strip()
                    try:
                        new_reward = float(new_reward)
                        if new_reward > 0:
                            self.config.mining_reward = new_reward
                            self.config.save_config()
                            print(color_text(f"✅ Mining reward updated to {new_reward}", COLORS['G']))
                        else:
                            print(color_text("❌ Reward must be positive", COLORS['R']))
                    except ValueError:
                        print(color_text("❌ Please enter a valid number", COLORS['R']))
                        
                elif choice == "3":
                    new_address = input(f"Enter new miner address (current: {self.config.miner_address}): ").strip()
                    if new_address:
                        self.config.miner_address = new_address
                        self.config.save_config()
                        print(color_text(f"✅ Miner address updated", COLORS['G']))
                    else:
                        print(color_text("❌ Address cannot be empty", COLORS['R']))
                        
                elif choice == "4":
                    break
                else:
                    print(color_text("❌ Invalid choice", COLORS['R']))
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(color_text(f"❌ Error: {e}", COLORS['R']))

    def show_mining_history(self):
        """Display mining history"""
        if not self.config.bills_mined:
            print(color_text("📭 No mining history yet", COLORS['O']))
            return
        
        print(color_text(f"\n📈 {COLORS['BOLD']}Mining History{COLORS['X']}", COLORS['I']))
        print("=" * 60)
        
        for i, bill in enumerate(reversed(self.config.bills_mined[-10:]), 1):
            print(color_text(f"\n#{i} | {bill['date']}", COLORS['B']))
            print(color_text(f"   Hash: {bill['block_hash'][:16]}...", COLORS['G']))
            print(color_text(f"   Reward: {bill['amount']} LUN", COLORS['Y']))
            print(color_text(f"   Transactions: {bill.get('transactions_mined', 0)}", COLORS['O']))
            if bill.get('verification_url'):
                print(color_text(f"   Verify: {bill['verification_url']}", COLORS['I']))

def main():
    """Main entry point"""
    try:
        node = LunaNode()
        node.show_menu()
    except KeyboardInterrupt:
        print(color_text("\n👋 Goodbye!", COLORS['G']))
    except Exception as e:
        print(color_text(f"❌ Fatal error: {e}", COLORS['R']))
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()