#!/usr/bin/env python3
"""
Luna Node - Enhanced with Reward Transaction Mining
Based on luna_sim.py with improved reward handling
"""

import requests
import threading
import time
import logging
import os
import random
import json
import hashlib
import secrets
import sys
from typing import List, Dict, Optional
import atexit

# Try to import CUDA modules
# Enhanced CUDA detection for RTX 4090
def setup_cuda():
    try:
        import pycuda.autoinit
        import pycuda.driver as cuda
        from pycuda.compiler import SourceModule
        import numpy as np
        
        # Test CUDA capability
        device = cuda.Device(0)
        print(f"🎮 CUDA Device: {device.name()}")
        print(f"🎮 Compute Capability: {device.compute_capability()}")
        print(f"🎮 Total Memory: {device.total_memory() // (1024**3)} GB")
        
        # RTX 4090 specific optimizations
        if "4090" in device.name():
            print("🚀 RTX 4090 detected - enabling high-performance mode")
            
        CUDA_AVAILABLE = True
        return CUDA_AVAILABLE
        
    except ImportError:
        print("❌ PyCUDA not installed. Install with: pip install pycuda")
        CUDA_AVAILABLE = False
    except Exception as e:
        print(f"❌ CUDA initialization failed: {e}")
        print("💡 Try: pip install pycuda")
        CUDA_AVAILABLE = False
    
    return CUDA_AVAILABLE

# Replace your existing CUDA import with:
CUDA_AVAILABLE = setup_cuda()
# -----------------------
# CONFIG
# -----------------------
BASE_URL = "https://bank.linglin.art/"

# HTTP endpoints
ENDPOINT_STATUS = f"{BASE_URL}/blockchain/status"
ENDPOINT_MEMPOOL_ADD = f"{BASE_URL}/mempool/add"
ENDPOINT_MEMPOOL_STATUS = f"{BASE_URL}/mempool/status"
ENDPOINT_BLOCKCHAIN_STATUS = f"{BASE_URL}/blockchain/status"
ENDPOINT_SUBMIT_BLOCK = f"{BASE_URL}/blockchain/submit-block"
ENDPOINT_BLOCKCHAIN = f"{BASE_URL}/blockchain"

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("luna_node")

# Colors for console output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    ORANGE = '\033[38;5;214m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def color_text(text, color):
    return f"{color}{text}{Colors.END}"

class ConfigManager:
    """Manage node configuration"""
    
    @staticmethod
    def get_data_dir():
        if getattr(sys, "frozen", False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_dir, "data")
    
    @staticmethod
    def save_json(filename, data):
        os.makedirs(ConfigManager.get_data_dir(), exist_ok=True)
        filepath = os.path.join(ConfigManager.get_data_dir(), filename)
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        return True
    
    @staticmethod
    def load_json(filename, default=None):
        if default is None:
            default = {}
        filepath = os.path.join(ConfigManager.get_data_dir(), filename)
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                return json.load(f)
        return default

class NodeConfig:
    """Node configuration with auto-setup"""
    
    def __init__(self):
        self.config_file = "node_config.json"
        self.load_config()
        
        # Auto-setup if no config exists
        if not hasattr(self, 'miner_address') or not self.miner_address:
            self.setup_new_node()
    
    def load_config(self):
        config = ConfigManager.load_json(
            self.config_file,
            {
                "miner_address": "LUN_e93d86a530870259_7fdd8f27",
                "difficulty": 1,
                "mining_reward": 1.0,
                "transaction_fee": 0.1,
                "auto_mine": False,
                "use_cuda": CUDA_AVAILABLE,
                "api_base_url": "https://bank.linglin.art/",
                "bills_mined": [],
                "created_at": time.time(),
                "last_sync": 0,
                "node_version": "2.1.0",
                "reward_transactions_mined": []  # Track reward transactions we've mined
            }
        )
        
        for key, value in config.items():
            setattr(self, key, value)
    
    def setup_new_node(self):
        """Interactive setup for new nodes"""
        print(color_text("\n🎯 Luna Node Setup", Colors.BOLD + Colors.CYAN))
        print("=" * 40)
        
        # Get wallet address
        while True:
            address = input(color_text("💰 Enter your wallet address: ", Colors.YELLOW)).strip()
            if address:
                self.miner_address = address
                break
            print(color_text("❌ Wallet address cannot be empty", Colors.RED))
        
        # Get difficulty
        while True:
            try:
                diff = input(color_text("🎯 Enter mining difficulty (1-8, default 4): ", Colors.YELLOW)).strip()
                if not diff:
                    diff = 4
                else:
                    diff = int(diff)
                if 1 <= diff <= 8:
                    self.difficulty = diff
                    break
                else:
                    print(color_text("❌ Difficulty must be between 1-8", Colors.RED))
            except ValueError:
                print(color_text("❌ Please enter a valid number", Colors.RED))
        
        # Ask about auto-mining
        auto_mine = input(color_text("🤖 Enable auto-mining? (y/N): ", Colors.YELLOW)).strip().lower()
        self.auto_mine = auto_mine in ['y', 'yes']
        
        # CUDA setup if available
        if CUDA_AVAILABLE:
            use_cuda = input(color_text("🎮 Use CUDA for mining? (Y/n): ", Colors.YELLOW)).strip().lower()
            self.use_cuda = use_cuda not in ['n', 'no']
        else:
            self.use_cuda = False
        
        self.save_config()
        print(color_text("✅ Node configuration saved!", Colors.GREEN))
    
    def save_config(self):
        config = {key: getattr(self, key) for key in [
            'miner_address', 'difficulty', 'mining_reward', 'transaction_fee',
            'auto_mine', 'use_cuda', 'api_base_url', 'bills_mined', 'created_at', 'last_sync', 
            'node_version', 'reward_transactions_mined'
        ]}
        ConfigManager.save_json(self.config_file, config)
    
    def add_bill(self, block_hash, amount, transactions_mined=0, reward_tx_hash=None):
        """Add a mined bill to history"""
        bill = {
            "block_hash": block_hash,
            "amount": amount,
            "timestamp": time.time(),
            "date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "transactions_mined": transactions_mined,
            "reward_tx_hash": reward_tx_hash
        }
        self.bills_mined.append(bill)
        
        # Keep only last 50 bills
        if len(self.bills_mined) > 50:
            self.bills_mined = self.bills_mined[-50:]
        
        self.save_config()
    
    def add_reward_transaction(self, reward_tx_hash, amount, block_hash):
        """Track reward transactions we've mined"""
        reward_tx = {
            "hash": reward_tx_hash,
            "amount": amount,
            "block_hash": block_hash,
            "timestamp": time.time(),
            "date": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.reward_transactions_mined.append(reward_tx)
        
        # Keep only last 100 reward transactions
        if len(self.reward_transactions_mined) > 100:
            self.reward_transactions_mined = self.reward_transactions_mined[-100:]
        
        self.save_config()
    
    def get_bills_summary(self):
        """Get summary of mined bills"""
        total_bills = len(self.bills_mined)
        total_reward = sum(bill["amount"] for bill in self.bills_mined)
        total_transactions = sum(bill.get("transactions_mined", 0) for bill in self.bills_mined)
        return total_bills, total_reward, total_transactions
    
    def get_rewards_summary(self):
        """Get summary of reward transactions mined"""
        total_rewards = len(self.reward_transactions_mined)
        total_amount = sum(reward["amount"] for reward in self.reward_transactions_mined)
        return total_rewards, total_amount

class BlockchainState:
    """Get the correct blockchain state with proper previous hash"""
    
    @staticmethod
    def get_next_block_info():
        """Get the correct next block info with ACTUAL previous hash"""
        try:
            # Get blockchain status
            status_response = requests.get(ENDPOINT_BLOCKCHAIN_STATUS, timeout=10)
            if status_response.status_code == 200:
                status_data = status_response.json()
                status_info = status_data.get('status', {})
                
                # Get actual blockchain to get the REAL previous hash
                blockchain_response = requests.get(ENDPOINT_BLOCKCHAIN, timeout=10)
                actual_blocks_count = 0
                actual_previous_hash = "0" * 64
                
                if blockchain_response.status_code == 200:
                    blockchain_data = blockchain_response.json()
                    actual_blocks_count = len(blockchain_data)
                    
                    # Get the ACTUAL hash of the last block
                    if actual_blocks_count > 0:
                        last_block = blockchain_data[-1]
                        actual_previous_hash = last_block.get('hash', '0' * 64)
                    else:
                        actual_previous_hash = "0"  # Genesis case
                
                # SERVER LOGIC: If blockchain has 1 block (genesis), it expects next block to be index 1
                reported_height = status_info.get('blocks', 0)
                difficulty = status_info.get('difficulty', 1)
                
                # The key fix: next_index should equal reported_height
                next_index = reported_height
                
                return {
                    'next_index': next_index,  # This matches server expectation
                    'previous_hash': actual_previous_hash,  # ACTUAL hash, not zeros!
                    'difficulty': difficulty,
                    'reported_height': reported_height,
                    'actual_blocks': actual_blocks_count
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to get blockchain info: {e}")
        
        return {'next_index': 0, 'previous_hash': '0' * 64, 'difficulty': 1, 'reported_height': 0, 'actual_blocks': 0}

class RealBlock:
    """Real block with exact server hash calculation"""
    
    def __init__(self, index, previous_hash, transactions, nonce=0, timestamp=None, miner="default_miner"):
        self.index = int(index)
        self.previous_hash = previous_hash
        self.timestamp = float(timestamp or time.time())
        self.transactions = transactions
        self.nonce = int(nonce)
        self.miner = miner
        self.hash = ""
        self.mining_time = 0

    def calculate_hash(self):
        """Calculate block hash using the EXACT server method"""
        # Based on analysis, the server uses sorted compact JSON
        block_data = {
            'index': self.index,
            'previous_hash': self.previous_hash,
            'timestamp': self.timestamp,
            'transactions': self.transactions,
            'nonce': self.nonce
        }
        
        # This should match the server's method
        block_string = json.dumps(block_data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(block_string.encode()).hexdigest()

    def mine_block(self, difficulty):
        """Mine block with proof-of-work"""
        if self.index == 0:  # Genesis block
            self.hash = "0" * 64
            return True
            
        target = "0" * difficulty
        start_time = time.time()
        
        print(color_text(f"⛏️ Mining Block #{self.index} | Target: {target}...", Colors.CYAN))
        print(color_text(f"   Previous hash: {self.previous_hash[:16]}...", Colors.BLUE))
        
        # Start from random position
        self.nonce = random.randint(0, 1000000)
        self.hash = self.calculate_hash()
        
        attempts = 0
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
            attempts += 1
            
            if attempts % 100000 == 0:
                hash_rate = attempts / (time.time() - start_time)
                print(color_text(f"   Attempts: {attempts:,} | Rate: {hash_rate:,.0f} H/s | Hash: {self.hash[:16]}...", Colors.YELLOW))
            
            if attempts > 2000000:
                print(color_text("🔄 Restarting mining with new nonce range...", Colors.YELLOW))
                self.nonce = random.randint(0, 1000000)
                attempts = 0

        self.mining_time = time.time() - start_time
        
        print(color_text(f"✅ Block mined! Time: {self.mining_time:.2f}s", Colors.GREEN))
        print(color_text(f"   Nonce: {self.nonce:,} | Hash: {self.hash}", Colors.GREEN))
        return True

    def to_dict(self):
        """Convert to server format"""
        return {
            "hash": self.hash,
            "index": self.index,
            "nonce": self.nonce,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "miner": self.miner
        }
class Block:
    """Block class for hash verification"""
    
    def __init__(self, index, previous_hash, transactions, nonce=0, timestamp=None):
        self.index = int(index)
        self.previous_hash = previous_hash
        self.timestamp = float(timestamp or time.time())
        self.transactions = transactions
        self.nonce = int(nonce)
        self.hash = ""
    
    def calculate_hash(self):
        """Calculate block hash using the EXACT server method"""
        # Based on analysis, the server uses sorted compact JSON
        block_data = {
            'index': self.index,
            'previous_hash': self.previous_hash,
            'timestamp': self.timestamp,
            'transactions': self.transactions,
            'nonce': self.nonce
        }
        
        # This should match the server's method
        block_string = json.dumps(block_data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(block_string.encode()).hexdigest()
class SmartMiner:
    """Optimized miner with fast reward transaction filtering"""
    
    def __init__(self, config):
        self.config = config
        self.miner_address = config.miner_address
        self.is_mining = False
        self.blocks_mined = 0
        
        # Caching for performance
        self._reward_cache = set()  # Fast lookup of mined reward signatures
        self._cache_timestamp = 0
        self._cache_ttl = 300  # 5 minutes cache TTL
    def broadcast_reward_transaction(self, reward_data):
        """Broadcast a reward transaction to the API - UPDATED WITH PROPER HASH"""
        try:
            print(color_text("🌐 Broadcasting reward transaction to API...", COLORS["B"]))

            # Generate a proper hash for the reward transaction
            timestamp = time.time()
            reward_id = f"reward_{int(timestamp)}_{secrets.token_hex(8)}"
            
            # Create hash from reward data to ensure uniqueness
            hash_data = f"reward:{reward_data.get('to','')}:{reward_data.get('amount',0)}:{reward_data.get('block_height',0)}:{timestamp}"
            reward_hash = hashlib.sha256(hash_data.encode()).hexdigest()

            # Create proper transaction structure
            reward_tx = {
                "type": "reward",
                "from": "Ling Country Treasury",  # Or "https://bank.linglin.art"
                "to": reward_data.get("to", ""),
                "amount": float(reward_data.get("amount", 0)),
                "description": reward_data.get("description", "Mining reward"),
                "block_height": int(reward_data.get("block_height", 0)),
                "timestamp": timestamp,
                "miner": reward_data.get("to", ""),  # Miner is the recipient
                "hash": reward_hash,  # Proper hash required by server
                "signature": reward_id,
                "transactions_mined": reward_data.get("transactions_mined", 0),
            }

            # Validate required fields
            if not reward_tx["to"]:
                print(color_text("❌ Cannot broadcast reward: missing 'to' address", COLORS["R"]))
                return False

            if reward_tx["amount"] <= 0:
                print(color_text("❌ Cannot broadcast reward: invalid amount", COLORS["R"]))
                return False

            # Validate the transaction before sending
            validation = validate_reward_transactions([reward_tx], reward_tx["block_height"])
            if not validation['valid']:
                print(color_text(f"❌ Reward transaction validation failed: {validation['error']}", COLORS["R"]))
                return False

            print(color_text(f"📤 Broadcasting reward transaction: {reward_hash[:16]}...", COLORS["B"]))
            print(color_text(f"   From: {reward_tx['from']}", COLORS["G"]))
            print(color_text(f"   To: {reward_tx['to']}", COLORS["G"]))
            print(color_text(f"   Amount: {reward_tx['amount']} LUN", COLORS["G"]))
            print(color_text(f"   Block: #{reward_tx['block_height']}", COLORS["G"]))

            # Use the broadcast endpoint (same as regular transactions)
            response = requests.post(
                f"{self.config.api_base_url}/api/transaction/broadcast",
                json=reward_tx,
                timeout=30,
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    print(color_text("✅ Reward transaction broadcasted successfully!", COLORS["G"]))
                    print(color_text(f"📝 Transaction hash: {reward_hash}", COLORS["B"]))
                    return True
                else:
                    print(color_text(f"❌ API returned error: {result.get('message', 'Unknown error')}", COLORS["R"]))
            else:
                print(color_text(f"❌ API returned status code: {response.status_code}", COLORS["R"]))
                print(color_text(f"📋 Response: {response.text}", COLORS["O"]))

        except Exception as e:
            print(color_text(f"❌ Error broadcasting reward transaction: {e}", COLORS["R"]))

        return False
    def _get_reward_signature(self, reward_tx):
        """Generate a unique signature for a reward transaction"""
        recipient = reward_tx.get('to')
        block_height = reward_tx.get('block_height')
        amount = reward_tx.get('amount')
        tx_hash = reward_tx.get('hash')
        
        # Use hash if available, otherwise create signature
        if tx_hash:
            return tx_hash
        return f"reward_{recipient}_{block_height}_{amount}"
    
    def _refresh_reward_cache(self):
        """Refresh the reward cache with current mined rewards"""
        current_time = time.time()
        if current_time - self._cache_timestamp < self._cache_ttl:
            return  # Cache still valid
        
        print(color_text("🔄 Refreshing reward cache...", Colors.BLUE))
        self._reward_cache.clear()
        
        # Add locally tracked rewards
        for reward in self.config.reward_transactions_mined:
            if reward.get('hash'):
                self._reward_cache.add(reward['hash'])
        
        # Add rewards from blockchain (limited to recent blocks for speed)
        try:
            blockchain_response = requests.get(ENDPOINT_BLOCKCHAIN, timeout=10)
            if blockchain_response.status_code == 200:
                blockchain_data = blockchain_response.json()
                
                # Only check recent blocks (last 50) for performance
                recent_blocks = blockchain_data[-50:] if len(blockchain_data) > 50 else blockchain_data
                
                for block in recent_blocks:
                    transactions = block.get('transactions', [])
                    for tx in transactions:
                        if tx.get('type') == 'reward':
                            signature = self._get_reward_signature(tx)
                            self._reward_cache.add(signature)
                
                print(color_text(f"✅ Reward cache updated: {len(self._reward_cache)} mined rewards", Colors.GREEN))
        
        except Exception as e:
            print(color_text(f"⚠️ Cache refresh warning: {e}", Colors.ORANGE))
        
        self._cache_timestamp = current_time
    
    def is_reward_already_mined(self, reward_tx):
        """Fast check if reward is already mined using cache"""
        # Refresh cache if needed
        self._refresh_reward_cache()
        
        signature = self._get_reward_signature(reward_tx)
        return signature in self._reward_cache
    
    def get_mempool_transactions(self):
        """Get transactions from mempool with fast reward filtering"""
        try:
            start_time = time.time()
            response = requests.get(ENDPOINT_MEMPOOL_STATUS, timeout=10)
            if response.status_code == 200:
                data = response.json()
                transactions = data.get('status', {}).get('transactions', [])
                
                # Pre-filter transactions by type
                valid_txs = []
                reward_txs = []
                
                for tx in transactions:
                    tx_type = tx.get('type')
                    if tx_type in ['transfer', 'GTX_Genesis']:
                        valid_txs.append(tx)
                    elif tx_type == 'reward':
                        reward_txs.append(tx)
                
                # Fast parallel processing of reward transactions
                unmined_rewards = self._filter_unmined_rewards_parallel(reward_txs)
                
                processing_time = time.time() - start_time
                print(color_text(f"📥 Transactions loaded in {processing_time:.2f}s: {len(valid_txs)} regular + {len(unmined_rewards)} unmined rewards", Colors.BLUE))
                
                return valid_txs + unmined_rewards
                
        except Exception as e:
            print(color_text(f"❌ Mempool error: {e}", Colors.RED))
        return []
    
    def _filter_unmined_rewards_parallel(self, reward_txs):
        """Filter unmined rewards using batch processing"""
        if not reward_txs:
            return []
        
        # Refresh cache first
        self._refresh_reward_cache()
        
        unmined_rewards = []
        skipped_count = 0
        
        for tx in reward_txs:
            if not self.is_reward_already_mined(tx):
                unmined_rewards.append(tx)
            else:
                skipped_count += 1
        
        if skipped_count > 0:
            print(color_text(f"⏭️  Skipped {skipped_count} already mined rewards", Colors.YELLOW))
        
        return unmined_rewards
    
    def scan_for_unmined_rewards(self, current_block_index):
        """Scan blockchain for unmined reward transactions - FIXED VERSION"""
        try:
            print(color_text("🔍 Scanning blockchain for unmined reward transactions...", Colors.BLUE))
            blockchain_response = requests.get(ENDPOINT_BLOCKCHAIN, timeout=10)
            if blockchain_response.status_code == 200:
                blockchain_data = blockchain_response.json()
                
                unmined_rewards = []
                for block in blockchain_data:
                    transactions = block.get('transactions', [])
                    for tx in transactions:
                        if tx.get('type') == 'reward':
                            # FIX: Only include rewards that belong to the CURRENT block we're mining
                            if tx.get('block_height') == current_block_index:
                                # Check if this reward hasn't been mined by us yet
                                if not self.is_reward_already_mined(tx):
                                    unmined_rewards.append(tx)
                                else:
                                    print(color_text(f"⏭️  Skipping mined reward in block {block.get('index')}: {tx.get('to')} for {tx.get('amount')} LUN", Colors.YELLOW))
                            else:
                                # Skip rewards from other blocks
                                print(color_text(f"⏭️  Skipping reward from wrong block {tx.get('block_height')} (mining block {current_block_index})", Colors.ORANGE))
                
                print(color_text(f"💰 Found {len(unmined_rewards)} unmined reward transactions for block #{current_block_index}", Colors.GREEN))
                return unmined_rewards
                
        except Exception as e:
            print(color_text(f"❌ Error scanning for rewards: {e}", Colors.RED))
        
        return []
    
    def mark_reward_as_mined(self, reward_tx, block_hash):
        """Fast marking of reward as mined"""
        try:
            signature = self._get_reward_signature(reward_tx)
            
            # Add to cache immediately
            self._reward_cache.add(signature)
            
            # Check if already in local history
            already_marked = any(
                r.get('hash') == signature for r in self.config.reward_transactions_mined
            )
            
            if not already_marked:
                reward_data = {
                    "hash": signature,
                    "recipient": reward_tx.get('to'),
                    "amount": reward_tx.get('amount'),
                    "block_height": reward_tx.get('block_height'),
                    "block_hash": block_hash,
                    "timestamp": time.time(),
                    "date": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                self.config.reward_transactions_mined.append(reward_data)
                
                # Keep history manageable
                if len(self.config.reward_transactions_mined) > 200:
                    self.config.reward_transactions_mined = self.config.reward_transactions_mined[-200:]
                
                self.config.save_config()
                print(color_text(f"✅ Marked reward as mined: {reward_tx.get('to')} for {reward_tx.get('amount')} LUN", Colors.GREEN))
                
        except Exception as e:
            print(color_text(f"❌ Error marking reward: {e}", Colors.RED))
    
    
    
    def should_include_reward_transaction(self, reward_tx):
        """Determine if we should include a reward transaction in our block"""
        # Don't include our own reward transactions
        if reward_tx.get('to') == self.miner_address or reward_tx.get('miner') == self.miner_address:
            return False
        
        # Check if reward transaction is already mined
        if self.is_reward_already_mined(reward_tx):
            return False
        
        return True
    def get_latest_block(self):
        """Get the latest block from the blockchain"""
        try:
            response = requests.get(ENDPOINT_BLOCKCHAIN, timeout=10)
            if response.status_code == 200:
                blockchain_data = response.json()
                if blockchain_data and len(blockchain_data) > 0:
                    return blockchain_data[-1]  # Return the last block
        except Exception as e:
            print(color_text(f"❌ Error getting latest block: {e}", Colors.RED))
        
        return None
    def mark_reward_as_mined(self, reward_tx, block_hash):
        """Mark a reward transaction as mined"""
        try:
            reward_tx_hash = reward_tx.get('hash')
            if not reward_tx_hash:
                # Create a signature if no hash exists
                reward_tx_hash = f"{reward_tx.get('to')}_{reward_tx.get('block_height')}_{reward_tx.get('amount')}"
            
            # Check if already marked
            already_marked = any(
                r.get('hash') == reward_tx_hash for r in self.config.reward_transactions_mined
            )
            
            if not already_marked:
                reward_data = {
                    "hash": reward_tx_hash,
                    "recipient": reward_tx.get('to'),
                    "amount": reward_tx.get('amount'),
                    "block_height": reward_tx.get('block_height'),
                    "block_hash": block_hash,
                    "timestamp": time.time(),
                    "date": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                self.config.reward_transactions_mined.append(reward_data)
                self.config.save_config()
                print(color_text(f"✅ Marked reward as mined: {reward_tx.get('to')} for {reward_tx.get('amount')} LUN", Colors.GREEN))
                
        except Exception as e:
            print(color_text(f"❌ Error marking reward as mined: {e}", Colors.RED))
    def sync_with_network(self):
        """Sync with network to get latest blockchain state"""
        print(color_text("🔄 Syncing with network...", Colors.BLUE))
        return BlockchainState.get_next_block_info()
    def mine_and_submit(self):
        """Complete mining process - WITH PROPER REWARD TRANSACTION MARKING"""
        try:
            # Get the CORRECT next block info with ACTUAL previous hash
            block_info = BlockchainState.get_next_block_info()
            next_index = block_info['next_index']
            previous_hash = block_info['previous_hash']
            difficulty = block_info['difficulty']
            
            print(color_text(f"🔗 Mining block #{next_index}", Colors.CYAN))
            print(color_text(f"   Previous hash: {previous_hash[:16]}...", Colors.BLUE))
            print(color_text(f"   Difficulty: {difficulty}", Colors.YELLOW))
            
            # Don't mine if we're at genesis and it already exists
            if next_index == 0:
                print(color_text("⏭️  Genesis block already exists, skipping...", Colors.YELLOW))
                return False
            
            # Get transactions from mempool (already filters mined rewards)
            mempool_txs = self.get_mempool_transactions()
            
            # Scan for unmined reward transactions in blockchain
            unmined_rewards = self.scan_for_unmined_rewards(next_index)
            
            # Combine all transactions
            all_external_txs = mempool_txs + unmined_rewards
            transaction_count = len(all_external_txs)
            
            # Calculate total reward
            base_reward = self.config.mining_reward
            fee_reward = transaction_count * self.config.transaction_fee
            total_reward = base_reward + fee_reward
            
            # Create our mining reward transaction
            our_reward_tx = self.create_reward_transaction(total_reward, next_index, transaction_count)
            
            # Combine transactions (our reward first, then others)
            all_transactions = [our_reward_tx] + all_external_txs
            
            print(color_text(f"💰 Total reward: {total_reward} LUN ({base_reward} base + {fee_reward} fees)", Colors.YELLOW))
            print(color_text(f"📊 Transactions: {transaction_count} external + 1 reward", Colors.BLUE))
            
            # Create and mine block with CORRECT previous hash
            block = RealBlock(next_index, previous_hash, all_transactions, miner=self.miner_address)
            
            print(color_text(f"⛏️ Starting mining of block #{next_index}", Colors.CYAN))
            if block.mine_block(difficulty):
                # Verify the hash before submitting
                verify_hash = block.calculate_hash()
                if verify_hash != block.hash:
                    print(color_text(f"❌ Hash verification failed: {block.hash} vs {verify_hash}", Colors.RED))
                    return False
                
                block_data = block.to_dict()
                print(color_text(f"📤 Submitting block #{next_index}", Colors.BLUE))
                
                # Get confirmation if not auto-mining
                if not self.config.auto_mine:
                    confirm = input(color_text("Submit this block? (y/N): ", Colors.BOLD)).strip().lower()
                    if confirm not in ['y', 'yes']:
                        print(color_text("❌ Submission cancelled", Colors.RED))
                        return False
                
                if self.submit_block(block_data):
                    self.blocks_mined += 1
                    self.sync_with_network()
                    
                    # Add to mining history
                    self.config.add_bill(block.hash, total_reward, transaction_count, our_reward_tx['hash'])
                    
                    # Track our reward transaction
                    self.config.add_reward_transaction(our_reward_tx['hash'], total_reward, block.hash)
                    
                    # PROPERLY MARK ALL EXTERNAL REWARD TRANSACTIONS AS MINED
                    reward_txs_marked = 0
                    for tx in all_external_txs:
                        if tx.get('type') == 'reward':
                            self.mark_reward_as_mined(tx, block.hash)
                            reward_txs_marked += 1
                            print(color_text(f"✅ Marked reward TX as mined: {tx.get('to')} for {tx.get('amount')} LUN", Colors.GREEN))
                    
                    if reward_txs_marked > 0:
                        print(color_text(f"🎯 Marked {reward_txs_marked} reward transactions as mined", Colors.MAGENTA))
                    
                    print(color_text(f"🎉 SUCCESS! Block #{next_index} accepted", Colors.GREEN))
                    print(color_text(f"💰 Reward: {total_reward} LUN", Colors.YELLOW))
                    print(color_text(f"📊 Transactions: {transaction_count}", Colors.BLUE))
                    print(color_text(f"⏱️  Time: {block.mining_time:.2f}s", Colors.CYAN))
                    print(color_text(f"🎯 Our Reward TX: {our_reward_tx['hash'][:16]}...", Colors.MAGENTA))
                    print(color_text(f"📝 Block Hash: {block.hash[:16]}...", Colors.CYAN))
                    return True
                else:
                    print(color_text(f"❌ Failed to submit block #{next_index}", Colors.RED))
            else:
                print(color_text(f"❌ Failed to mine block #{next_index}", Colors.RED))
            
            return False
            
        except Exception as e:
            print(color_text(f"💥 Mining error: {e}", Colors.RED))
            import traceback
            traceback.print_exc()
            return False
    def submit_block(self, block_data):
        """Submit mined block to the API with confirmation"""
        try:
            print(color_text("📤 Submitting block to API...", Colors.BLUE))
            
            # Pre-submission validation
            if not self.validate_block_before_submission(block_data):
                print(color_text("❌ Block validation failed", Colors.RED))
                return False
            
            # Submit to the blockchain API endpoint
            response = requests.post(
                f"{self.config.api_base_url}/blockchain/submit-block",
                json=block_data,
                timeout=30
            )
            
            if response.status_code == 201:
                result = response.json()
                if result.get("success"):
                    print(color_text("✅ Block submitted successfully!", Colors.GREEN))
                    
                    # Wait for confirmation
                    if self.wait_for_block_confirmation(block_data['hash']):
                        print(color_text("🎉 Block confirmed on network!", Colors.GREEN))
                        return True
                    else:
                        print(color_text("⚠️ Block submitted but not yet confirmed", Colors.ORANGE))
                        return True  # Still return True as submission was successful
                else:
                    error_msg = result.get('error', 'Unknown error')
                    print(color_text(f"❌ Block rejected: {error_msg}", Colors.RED))
            else:
                print(color_text(f"❌ HTTP {response.status_code}: {response.text}", Colors.RED))
                
        except Exception as e:
            print(color_text(f"💥 Submission error: {e}", Colors.RED))
        
        return False

    def validate_block_before_submission(self, block_data):
        """Validate block before submitting to API"""
        try:
            required_fields = ['index', 'previous_hash', 'timestamp', 'transactions', 'nonce', 'hash']
            
            # Check required fields
            for field in required_fields:
                if field not in block_data:
                    print(color_text(f"❌ Missing required field: {field}", Colors.RED))
                    return False
            
            # Validate hash
            if not self.verify_block_hash(block_data):
                print(color_text("❌ Block hash verification failed", Colors.RED))
                return False
                
            # Validate index is sequential
            latest_block = self.get_latest_block()
            if latest_block and hasattr(latest_block, 'index'):
                expected_index = latest_block.index + 1
                if block_data['index'] != expected_index:
                    print(color_text(f"❌ Block index mismatch. Expected: {expected_index}, Got: {block_data['index']}", Colors.RED))
                    return False
            
            print(color_text("✅ Block validation passed", Colors.GREEN))
            return True
            
        except Exception as e:
            print(color_text(f"❌ Validation error: {e}", Colors.RED))
            return False

    def verify_block_hash(self, block_data):
        """Verify that the block hash is correct"""
        try:
            # Recreate the block hash calculation (must match server method)
            temp_block = Block(
                block_data['index'],
                block_data['previous_hash'],
                block_data['transactions'],
                block_data['nonce'],
                block_data['timestamp']
            )
            
            calculated_hash = temp_block.calculate_hash()
            if calculated_hash != block_data['hash']:
                print(color_text(f"❌ Hash mismatch: {calculated_hash} vs {block_data['hash']}", Colors.RED))
                return False
                
            return True
        except Exception as e:
            print(color_text(f"❌ Hash verification error: {e}", Colors.RED))
            return False

    def wait_for_block_confirmation(self, block_hash, max_attempts=10, delay=3):
        """Wait for block to be confirmed on the network"""
        print(color_text(f"⏳ Waiting for block confirmation...", Colors.BLUE))
        
        for attempt in range(max_attempts):
            try:
                # Check if block exists in the blockchain
                response = requests.get(
                    f"{self.config.api_base_url}/blockchain",
                    timeout=10
                )
                
                if response.status_code == 200:
                    blockchain_data = response.json()
                    if isinstance(blockchain_data, list):
                        # Look for our block in the chain
                        for block in blockchain_data:
                            if block.get('hash') == block_hash:
                                print(color_text(f"✅ Block found at position {block.get('index')}", Colors.GREEN))
                                return True
                    
                    print(color_text(f"🔍 Confirmation attempt {attempt + 1}/{max_attempts}...", Colors.BLUE))
                
                time.sleep(delay)
                
            except Exception as e:
                print(color_text(f"⚠️ Confirmation check failed: {e}", Colors.ORANGE))
                time.sleep(delay)
        
        print(color_text("❌ Block confirmation timeout", Colors.RED))
        return False

    def get_submission_confirmation(self):
        """Get user confirmation before submitting block"""
        if not self.config.auto_mine:
            print(color_text("\n⚠️  BLOCK READY FOR SUBMISSION", Colors.YELLOW))
            print(color_text("=" * 50, Colors.YELLOW))
            print(color_text(f"📦 Block #{self.get_latest_block().index + 1}", Colors.BLUE))
            print(color_text(f"⛏️  Miner: {self.config.miner_address}", Colors.GREEN))
            print(color_text(f"📊 Transactions: {len(self.blockchain.mempool)}", Colors.ORANGE))
            print(color_text("=" * 50, Colors.YELLOW))
            
            try:
                confirm = input(color_text("Submit this block? (y/N): ", Colors.BOLD)).strip().lower()
                return confirm in ['y', 'yes']
            except KeyboardInterrupt:
                print(color_text("\n❌ Submission cancelled", Colors.RED))
                return False
            except Exception:
                return False
        
        # Auto-confirm if auto-mining is enabled
        return True
    def create_reward_transaction(self, amount, block_height, transaction_count=0):
        """Create mining reward transaction with proper structure"""
        # FIX: Use the CURRENT block height, not previous
        current_block_height = block_height
        
        reward_data = f"reward_{self.miner_address}_{amount}_{current_block_height}_{transaction_count}_{time.time()}"
        reward_tx_hash = hashlib.sha256(reward_data.encode()).hexdigest()
        
        return {
            "type": "reward",
            "to": self.miner_address,
            "from": "Ling Country Treasury",
            "amount": float(amount),
            "timestamp": time.time(),
            "block_height": int(current_block_height),  # FIX: Use current block height
            "description": f"Mining reward for block {current_block_height} with {transaction_count} transactions",
            "transactions_included": transaction_count,
            "miner": self.miner_address,
            "fee_reward": float(transaction_count * self.config.transaction_fee),
            "hash": reward_tx_hash,
            "signature": f"reward_{reward_tx_hash[:16]}"
        }

    def start_auto_mining(self):
        """Start auto-mining loop"""
        self.is_mining = True
        print(color_text(f"🚀 Starting auto-miner: {self.miner_address}", Colors.GREEN))
        
        consecutive_failures = 0
        
        while self.is_mining:
            success = self.mine_and_submit()
            
            if success:
                consecutive_failures = 0
                time.sleep(10)  # Wait before next block
            else:
                consecutive_failures += 1
                if consecutive_failures >= 3:
                    print(color_text("💤 Multiple failures, taking longer break...", Colors.YELLOW))
                    time.sleep(30)
                    consecutive_failures = 0
                else:
                    time.sleep(15)
    
    def stop_mining(self):
        self.is_mining = False
        print(color_text(f"🛑 Miner stopped. Blocks mined: {self.blocks_mined}", Colors.YELLOW))

class LunaNode:
    """Main Luna Node class"""
    
    def __init__(self):
        self.config = NodeConfig()
        self.miner = SmartMiner(self.config)
        self.running = True
        self.auto_mine_thread = None
        
        # Register cleanup
        atexit.register(self.cleanup)
        
        self.show_welcome()
        self.auto_sync()
        
        # Start auto-mining if enabled
        if self.config.auto_mine:
            self.toggle_auto_mine()
    
    def show_welcome(self):
        """Show welcome message and status"""
        print(color_text(f"\n🌙 Luna Node v{self.config.node_version}", Colors.BOLD + Colors.CYAN))
        print("=" * 50)
        print(color_text(f"⛏️  Miner: {self.config.miner_address}", Colors.GREEN))
        print(color_text(f"🎯 Difficulty: {self.config.difficulty}", Colors.YELLOW))
        print(color_text(f"💰 Base Reward: {self.config.mining_reward} LUN", Colors.BLUE))
        print(color_text(f"💸 Transaction Fee: {self.config.transaction_fee} LUN", Colors.MAGENTA))
        print(color_text(f"🤖 Auto-mine: {'Enabled' if self.config.auto_mine else 'Disabled'}", Colors.CYAN))
        
        # Show mining history summary
        total_bills, total_reward, total_txs = self.config.get_bills_summary()
        total_rewards, total_reward_amount = self.config.get_rewards_summary()
        
        print(color_text(f"📈 Bills Mined: {total_bills}", Colors.GREEN))
        print(color_text(f"💰 Total Reward: {total_reward} LUN", Colors.YELLOW))
        print(color_text(f"📊 Total Transactions: {total_txs}", Colors.BLUE))
        print(color_text(f"🎯 Reward TXs Mined: {total_rewards}", Colors.MAGENTA))
    
    def auto_sync(self):
        """Auto-sync with network on startup"""
        print(color_text("\n🔄 Syncing with network...", Colors.BLUE))
        try:
            block_info = BlockchainState.get_next_block_info()
            print(color_text(f"📊 Network height: {block_info['reported_height']}", Colors.GREEN))
            print(color_text(f"🎯 Network difficulty: {block_info['difficulty']}", Colors.YELLOW))
            print(color_text(f"🔗 Last block hash: {block_info['previous_hash'][:16]}...", Colors.BLUE))
            
            # Update last sync time
            self.config.last_sync = time.time()
            self.config.save_config()
            
        except Exception as e:
            print(color_text(f"❌ Sync failed: {e}", Colors.RED))
    
    def toggle_auto_mine(self):
        """Toggle auto-mining on/off"""
        if self.miner.is_mining:
            self.miner.stop_mining()
            self.config.auto_mine = False
            print(color_text("⏹️  Auto-mining disabled", Colors.YELLOW))
        else:
            self.config.auto_mine = True
            self.auto_mine_thread = threading.Thread(target=self.miner.start_auto_mining, daemon=True)
            self.auto_mine_thread.start()
            print(color_text("✅ Auto-mining enabled", Colors.GREEN))
        
        self.config.save_config()
    
    def mine_once(self):
        """Mine a single block"""
        if self.miner.is_mining:
            print(color_text("⚠️  Auto-mining is running. Stop it first or wait for next block.", Colors.YELLOW))
            return
        
        print(color_text("\n⛏️  Mining single block...", Colors.CYAN))
        self.miner.mine_and_submit()
    
    def show_status(self):
        """Show node status"""
        print(color_text(f"\n📊 Node Status", Colors.BOLD + Colors.CYAN))
        print("=" * 40)
        
        # Network info
        try:
            block_info = BlockchainState.get_next_block_info()
            print(color_text(f"🌐 Network Height: {block_info['reported_height']}", Colors.BLUE))
            print(color_text(f"🎯 Network Difficulty: {block_info['difficulty']}", Colors.YELLOW))
            print(color_text(f"🔗 Previous Hash: {block_info['previous_hash'][:16]}...", Colors.BLUE))
        except:
            print(color_text("❌ Network unreachable", Colors.RED))
        
        # Miner info
        print(color_text(f"⛏️  Miner: {self.config.miner_address}", Colors.GREEN))
        print(color_text(f"📈 Blocks Mined: {self.miner.blocks_mined}", Colors.GREEN))
        print(color_text(f"🤖 Auto-mine: {'Running' if self.miner.is_mining else 'Stopped'}", Colors.MAGENTA))
        
        # Mining history
        total_bills, total_reward, total_txs = self.config.get_bills_summary()
        total_rewards, total_reward_amount = self.config.get_rewards_summary()
        
        print(color_text(f"💰 Total Reward: {total_reward} LUN", Colors.YELLOW))
        print(color_text(f"📊 Total Transactions: {total_txs}", Colors.BLUE))
        print(color_text(f"🎯 Reward TXs Mined: {total_rewards}", Colors.MAGENTA))
    
    def show_bills(self):
        """Show mining history"""
        if not self.config.bills_mined:
            print(color_text("📭 No bills mined yet", Colors.YELLOW))
            return
        
        total_bills, total_reward, total_txs = self.config.get_bills_summary()
        
        print(color_text(f"\n📈 Mining History", Colors.BOLD + Colors.CYAN))
        print("=" * 60)
        print(color_text(f"Total Bills: {total_bills} | Total Reward: {total_reward} LUN | Total Transactions: {total_txs}", Colors.GREEN))
        print()
        
        for i, bill in enumerate(reversed(self.config.bills_mined[-10:]), 1):
            print(color_text(f"#{i} | {bill['date']}", Colors.BOLD))
            print(color_text(f"   Hash: {bill['block_hash'][:16]}...", Colors.BLUE))
            print(color_text(f"   Reward: {bill['amount']} LUN", Colors.YELLOW))
            print(color_text(f"   Transactions: {bill.get('transactions_mined', 0)}", Colors.GREEN))
            if bill.get('reward_tx_hash'):
                print(color_text(f"   Reward TX: {bill['reward_tx_hash'][:16]}...", Colors.MAGENTA))
            print()
    
    def show_rewards(self):
        """Show reward transaction history"""
        if not self.config.reward_transactions_mined:
            print(color_text("📭 No reward transactions mined yet", Colors.YELLOW))
            return
        
        total_rewards, total_amount = self.config.get_rewards_summary()
        
        print(color_text(f"\n🎯 Reward Transactions Mined", Colors.BOLD + Colors.MAGENTA))
        print("=" * 60)
        print(color_text(f"Total Rewards: {total_rewards} | Total Amount: {total_amount} LUN", Colors.GREEN))
        print()
        
        for i, reward in enumerate(reversed(self.config.reward_transactions_mined[-10:]), 1):
            print(color_text(f"#{i} | {reward['date']}", Colors.BOLD))
            print(color_text(f"   Hash: {reward['hash'][:16]}...", Colors.MAGENTA))
            print(color_text(f"   Amount: {reward['amount']} LUN", Colors.YELLOW))
            print(color_text(f"   Block: {reward['block_hash'][:16]}...", Colors.BLUE))
            print()
    
    def show_menu(self):
        """Display main menu"""
        while self.running:
            print(color_text(f"\n🌙 Luna Node Menu", Colors.BOLD + Colors.CYAN))
            print("=" * 40)
            print(color_text("1. 📊 Show Status", Colors.BLUE))
            print(color_text("2. ⛏️  Mine Single Block", Colors.GREEN))
            print(color_text("3. 🤖 Toggle Auto-mining", Colors.MAGENTA))
            print(color_text("4. 📈 Show Mining History", Colors.YELLOW))
            print(color_text("5. 🎯 Show Reward Transactions", Colors.MAGENTA))
            print(color_text("6. 🔄 Sync with Network", Colors.CYAN))
            print(color_text("7. 🚪 Exit", Colors.RED))
            
            try:
                choice = input(color_text("\n🎯 Enter your choice (1-7): ", Colors.BOLD)).strip()
                
                if choice == "1":
                    self.show_status()
                elif choice == "2":
                    self.mine_once()
                elif choice == "3":
                    self.toggle_auto_mine()
                elif choice == "4":
                    self.show_bills()
                elif choice == "5":
                    self.show_rewards()
                elif choice == "6":
                    self.auto_sync()
                elif choice == "7":
                    print(color_text("👋 Goodbye!", Colors.GREEN))
                    self.running = False
                else:
                    print(color_text("❌ Invalid choice", Colors.RED))
                    
            except KeyboardInterrupt:
                print(color_text("\n👋 Goodbye!", Colors.GREEN))
                self.running = False
            except Exception as e:
                print(color_text(f"❌ Error: {e}", Colors.RED))
    
    def cleanup(self):
        """Cleanup on exit"""
        self.running = False
        if self.miner:
            self.miner.stop_mining()
        if self.auto_mine_thread and self.auto_mine_thread.is_alive():
            self.auto_mine_thread.join(timeout=1)

def main():
    """Main entry point"""
    try:
        node = LunaNode()
        node.show_menu()
    except KeyboardInterrupt:
        print(color_text("\n👋 Goodbye!", Colors.GREEN))
    except Exception as e:
        print(color_text(f"❌ Fatal error: {e}", Colors.RED))
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()