#!/usr/bin/env python3
"""
Luna Node - Real Mining with ROYGBIV Progress & P2P Pool Support
"""

import os
import json
import time
import threading
import hashlib
import uuid
import requests
from tqdm import tqdm

# ROYGBIV Color Codes
COLORS = {
    "R": "\033[91m",  # Red
    "O": "\033[93m",  # Orange/Yellow
    "Y": "\033[93m",  # Yellow
    "G": "\033[92m",  # Green
    "B": "\033[94m",  # Blue
    "I": "\033[95m",  # Indigo/Magenta
    "V": "\033[95m",  # Violet
    "X": "\033[0m",   # Reset
}

def color_text(text, color):
    return f"{color}{text}{COLORS['X']}"



class Block:
    def __init__(self, index, previous_hash, transactions, nonce=0, timestamp=None):
        self.index = int(index)
        self.previous_hash = previous_hash
        self.timestamp = int(timestamp or time.time())  # Ensure integer timestamp
        self.transactions = transactions
        self.nonce = int(nonce)
        self.hash = self.calculate_hash()
        self.mining_time = 0

    def calculate_hash(self):
        """Calculate block hash - MATCHING BLOCKCHAIN DAEMON"""
        # Use the EXACT same format as blockchain_daemon.calculate_block_hash
        block_data = {
            'index': self.index,
            'previous_hash': self.previous_hash,
            'timestamp': self.timestamp,
            'transactions': json.dumps(self.transactions, sort_keys=True),
            'nonce': self.nonce
        }
        block_string = json.dumps(block_data, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def mine_block(self, difficulty, progress_callback=None):
        target = "0" * difficulty
        start_time = time.time()
        hashes_tried = 0
        hash_rates = []
        last_update = start_time

        print(color_text(f"\n🎯 Mining Block #{self.index} | Difficulty: {difficulty}", COLORS["B"]))
        
        # ROYGBIV colors for progress
        roygbiv_colors = [COLORS["R"], COLORS["O"], COLORS["Y"], COLORS["G"], COLORS["B"], COLORS["I"], COLORS["V"]]
        
        with tqdm(
            desc=color_text("⛏️  Mining", COLORS["Y"]),
            bar_format="{l_bar}%s{bar}%s{r_bar}" % (COLORS["B"], COLORS["X"]),
            ncols=80,
            unit="hash",
            unit_scale=True
        ) as pbar:
            
            while self.hash[:difficulty] != target:
                self.nonce += 1
                hashes_tried += 1
                self.hash = self.calculate_hash()
                
                current_time = time.time()
                if current_time - last_update >= 0.5:  # Update every 500ms
                    elapsed = current_time - start_time
                    current_hash_rate = hashes_tried / elapsed
                    hash_rates.append(current_hash_rate)
                    avg_hash_rate = sum(hash_rates[-10:]) / min(10, len(hash_rates))
                    
                    # ROYGBIV progress calculation
                    progress_color = roygbiv_colors[int((self.nonce / 1000) % len(roygbiv_colors))]
                    
                    # Update progress bar
                    hash_rate_str = f"{avg_hash_rate:,.0f} H/s"
                    if avg_hash_rate > 1000:
                        hash_rate_str = f"{avg_hash_rate/1000:,.1f} kH/s"
                    
                    pbar.set_description(f"{progress_color}⛏️  {hash_rate_str}{COLORS['X']}")
                    pbar.update(hashes_tried - pbar.n)
                    pbar.refresh()
                    
                    last_update = current_time
                    
                    if progress_callback:
                        progress_callback(hashes_tried, avg_hash_rate, self.nonce)

        self.mining_time = time.time() - start_time
        pbar.close()
        print(color_text(f"✅ Block mined in {self.mining_time:.2f}s with {hashes_tried:,} hashes", COLORS["G"]))
        return True

class LunaNode:
    def __init__(self):
        self.api_base = "https://bank.linglin.art"
        self.data_dir = self.get_data_dir()
        self.config_file = os.path.join(self.data_dir, "miner_config.json")
        self.config = self.load_config()
        self.mempool = []
        self.running = True
        self.is_mining = False
        self.pool_peers = []
        self.mining_pool = False
        
        print(color_text(f"🌙 Luna Miner v1.0.0", COLORS["I"]))
        print(color_text(f"⛏️  Miner: {self.config['miner_address']}", COLORS["G"]))
        print(color_text(f"🔗 Mode: {'Pool Mining' if self.mining_pool else 'Solo Mining'}", COLORS["B"]))
        
        # Start services
        self.start_auto_sync()
        if self.mining_pool:
            self.connect_to_pool()
    
    def get_data_dir(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(base_dir, "data")
        os.makedirs(data_dir, exist_ok=True)
        return data_dir
    
    def load_config(self):
        default_config = {
            "node_id": str(uuid.uuid4()),
            "miner_address": f"LUN_{hashlib.sha256(str(time.time()).encode()).hexdigest()[:16]}",
            "created_at": time.time(),
            "bills_mined": [],
            "auto_mine": False,
            "mined_transactions": {},
            "mining_pool": False,
            "pool_address": "http://localhost:9333",
            "difficulty": 4
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    for key, value in default_config.items():
                        if key not in loaded_config:
                            loaded_config[key] = value
                    self.mining_pool = loaded_config.get('mining_pool', False)
                    return loaded_config
        except Exception as e:
            print(color_text(f"Config load error: {e}", COLORS["R"]))
        
        self.save_config(default_config)
        self.mining_pool = default_config['mining_pool']
        return default_config
    
    def save_config(self, config=None):
        config = config or self.config
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(color_text(f"Config save error: {e}", COLORS["R"]))
    
    def connect_to_pool(self):
        """Connect to mining pool"""
        try:
            pool_url = self.config.get('pool_address')
            print(color_text(f"🔗 Connecting to pool: {pool_url}", COLORS["B"]))
            
            response = requests.post(
                f"{pool_url}/pool/join",
                json={
                    "miner_address": self.config['miner_address'],
                    "node_id": self.config['node_id']
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    self.pool_peers = result.get('peers', [])
                    print(color_text(f"✅ Connected to pool with {len(self.pool_peers)} peers", COLORS["G"]))
                    return True
        except Exception as e:
            print(color_text(f"❌ Pool connection failed: {e}", COLORS["R"]))
        
        return False
    
    def get_work_from_pool(self):
        """Get mining work from pool"""
        try:
            pool_url = self.config.get('pool_address')
            response = requests.get(f"{pool_url}/pool/work", timeout=10)
            
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return None
    
    def submit_work_to_pool(self, block_data):
        """Submit mined block to pool"""
        try:
            pool_url = self.config.get('pool_address')
            response = requests.post(
                f"{pool_url}/pool/submit",
                json=block_data,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return None
    
    def start_auto_sync(self):
        def sync_worker():
            while self.running:
                try:
                    self.sync_mempool()
                    if self.config.get('auto_mine', False) and not self.is_mining:
                        self.mine_from_mempool()
                    time.sleep(10)
                except Exception as e:
                    print(color_text(f"Sync error: {e}", COLORS["R"]))
                    time.sleep(30)
        
        threading.Thread(target=sync_worker, daemon=True).start()
        print(color_text("🔄 Auto-sync started", COLORS["B"]))
    
    def sync_mempool(self):
        try:
            response = requests.get(f"{self.api_base}/mempool", timeout=10)
            if response.status_code == 200:
                new_mempool = response.json()
                if len(new_mempool) != len(self.mempool):
                    print(color_text(f"📥 Mempool: {len(new_mempool)} transactions", COLORS["G"]))
                self.mempool = new_mempool
                return True
        except Exception as e:
            print(color_text(f"❌ Sync failed: {e}", COLORS["R"]))
        return False

    def get_tx_signature(self, tx):
        return tx.get('signature') or tx.get('serial_number') or hashlib.sha256(json.dumps(tx, sort_keys=True).encode()).hexdigest()[:32]
    def debug_block_submission(self, block_data):
        """Debug why block submission might be failing"""
        print(color_text("\n🔍 Debugging Block Submission", COLORS["B"]))
        
        try:
            # Test validation with the daemon
            test_url = f"{self.api_base}/api/blockchain/validate"
            response = requests.post(test_url, json=block_data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                print(color_text(f"✅ Validation API Response: {result}", COLORS["G"]))
            else:
                print(color_text(f"❌ Validation API HTTP {response.status_code}", COLORS["R"]))
                print(color_text(f"Response: {response.text}", COLORS["R"]))
                
        except Exception as e:
            print(color_text(f"❌ Validation test failed: {e}", COLORS["R"]))
        
        # Check the exact block format
        print(color_text("\n📦 Block Data Being Sent:", COLORS["Y"]))
        for key, value in block_data.items():
            if key == "transactions":
                print(color_text(f"   {key}: {len(value)} transactions", COLORS["B"]))
                for i, tx in enumerate(value[:3]):  # Show first 3 transactions
                    tx_type = tx.get('type', 'unknown')
                    print(color_text(f"     {i+1}. {tx_type}: {tx.get('hash', 'no_hash')[:16]}...", COLORS["B"]))
            elif key == "hash":
                print(color_text(f"   {key}: {value[:20]}...", COLORS["B"]))
            else:
                print(color_text(f"   {key}: {value} (type: {type(value)})", COLORS["B"]))
    def mine_from_mempool(self):
        if self.is_mining:
            print(color_text("⚠️  Mining already in progress", COLORS["O"]))
            return False
        
        if not self.mempool:
            print(color_text("📭 Mempool is empty", COLORS["O"]))
            return False
        
        # DEBUG: Check actual blockchain state first
        actual_blocks = self.debug_blockchain_state()
        
        self.is_mining = True
        try:
            # Get unmined transactions
            mined_txs = self.config.get('mined_transactions', {})
            unmined_txs = [tx for tx in self.mempool if self.get_tx_signature(tx) not in mined_txs]
            
            if not unmined_txs:
                print(color_text("ℹ️  No unmined transactions", COLORS["B"]))
                return False
            
            print(color_text(f"⛏️  Mining {len(unmined_txs)} transactions...", COLORS["G"]))
            
            # Show transaction types
            tx_types = {}
            for tx in unmined_txs:
                tx_type = tx.get('type', 'unknown')
                tx_types[tx_type] = tx_types.get(tx_type, 0) + 1
            
            for tx_type, count in tx_types.items():
                print(color_text(f"   - {count} {tx_type}", COLORS["Y"]))
            
            # Get CORRECT blockchain info
            block_index, previous_hash = self.get_correct_blockchain_info()
            
            # Safety check: don't mine if we don't have valid info
            if block_index is None or previous_hash is None:
                print(color_text("❌ Cannot get valid blockchain info, cannot mine", COLORS["R"]))
                self.is_mining = False
                return False
            
            if previous_hash == "0" * 64:
                print(color_text("🆕 Mining genesis block (no previous blocks)", COLORS["B"]))
            
            # Limit transactions to reasonable number for first block
            if block_index == 1 and len(unmined_txs) > 100:
                print(color_text(f"⚠️  Limiting to 100 transactions for first block", COLORS["O"]))
                unmined_txs = unmined_txs[:100]
            
            # Add reward transaction
            base_reward = 1.0
            bonus_per_tx = 0.1
            total_reward = base_reward + (bonus_per_tx * len(unmined_txs))
            
            reward_tx = {
                "type": "reward",
                "to": self.config['miner_address'],  # Use 'to' instead of 'miner'
                "amount": total_reward,
                "timestamp": int(time.time()),
                "block_height": block_index,
                "description": f"Mining reward for block {block_index}"
            }
            
            all_transactions = unmined_txs + [reward_tx]
            
            # Create and mine block
            difficulty = self.config.get('difficulty', 4)
            new_block = Block(block_index, previous_hash, all_transactions)
            
            def mining_progress(hashes_tried, hash_rate, nonce):
                pass  # tqdm handles progress
            
            start_time = time.time()
            if new_block.mine_block(difficulty, mining_progress):
                mining_time = time.time() - start_time
                
                # Submit to API
                block_data = {
                    "index": new_block.index,
                    "timestamp": new_block.timestamp,
                    "transactions": new_block.transactions,
                    "previous_hash": new_block.previous_hash,
                    "nonce": new_block.nonce,
                    "hash": new_block.hash,
                    "miner": self.config['miner_address']
                }
                
                # DEBUG: Show what we're submitting
                print(color_text(f"\n📤 Submitting Block #{new_block.index}:", COLORS["B"]))
                print(color_text(f"   Previous Hash: {new_block.previous_hash[:20]}...", COLORS["Y"]))
                print(color_text(f"   New Hash: {new_block.hash[:20]}...", COLORS["G"]))
                print(color_text(f"   Transactions: {len(new_block.transactions)}", COLORS["B"]))
                
                # Submit the block
                try:
                    submit_endpoints = [
                        f"{self.api_base}/api/blockchain/submit-block",
                        f"{self.api_base}/blockchain/submit-block"
                    ]
                    
                    for endpoint in submit_endpoints:
                        try:
                            print(color_text(f"📤 Trying submission to: {endpoint}", COLORS["B"]))
                            response = requests.post(
                                endpoint,
                                json=block_data,
                                timeout=30
                            )
                            
                            print(color_text(f"📤 Submission Response: {response.status_code}", COLORS["Y"]))
                            
                            if response.status_code == 201:
                                result = response.json()
                                if result.get('success'):
                                    # Update mined transactions
                                    for tx in unmined_txs:
                                        if self.get_tx_signature(tx):
                                            mined_txs[self.get_tx_signature(tx)] = time.time()
                                    
                                    # Add to mining history
                                    bill = {
                                        'block_hash': new_block.hash,
                                        'amount': total_reward,
                                        'timestamp': time.time(),
                                        'transactions': len(unmined_txs),
                                        'date': time.strftime("%Y-%m-%d %H:%M:%S"),
                                        'mining_time': mining_time,
                                        'difficulty': difficulty
                                    }
                                    self.config['bills_mined'].append(bill)
                                    
                                    # Keep only last 50 bills
                                    if len(self.config['bills_mined']) > 50:
                                        self.config['bills_mined'] = self.config['bills_mined'][-50:]
                                    
                                    self.config['mined_transactions'] = mined_txs
                                    self.save_config()
                                    
                                    print(color_text(f"✅ Block #{new_block.index} accepted! Reward: {total_reward} LUN", COLORS["G"]))
                                    self.is_mining = False
                                    return True
                                else:
                                    print(color_text(f"❌ Block rejected: {result.get('error', 'Unknown error')}", COLORS["R"]))
                            else:
                                print(color_text(f"❌ HTTP Error {response.status_code}: {response.text}", COLORS["R"]))
                                
                        except Exception as e:
                            print(color_text(f"❌ Submission to {endpoint} failed: {e}", COLORS["R"]))
                            continue
                    
                    print(color_text("❌ All submission endpoints failed", COLORS["R"]))
                        
                except Exception as e:
                    print(color_text(f"❌ API submission failed: {e}", COLORS["R"]))
                
        except Exception as e:
            print(color_text(f"❌ Mining error: {e}", COLORS["R"]))
        finally:
            self.is_mining = False
        
        return False
    def get_correct_blockchain_info(self):
        """Get the correct blockchain info for mining"""
        try:
            # Try multiple endpoints to get blockchain status
            endpoints_to_try = [
                f"{self.api_base}/api/blockchain/status",
                f"{self.api_base}/blockchain/status",
                f"{self.api_base}/api/blockchain/latest-block",
                f"{self.api_base}/blockchain/latest-block"
            ]
            
            for endpoint in endpoints_to_try:
                try:
                    print(color_text(f"🔗 Trying endpoint: {endpoint}", COLORS["B"]))
                    response = requests.get(endpoint, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Handle different response formats
                        if 'status' in data:
                            # /api/blockchain/status format
                            status_data = data.get('status', {})
                            current_height = status_data.get('blocks', 0)
                            latest_hash = status_data.get('latest_hash', '0' * 64)
                        elif 'block' in data:
                            # /api/blockchain/latest-block format  
                            block_data = data.get('block', {})
                            current_height = block_data.get('index', 0)
                            latest_hash = block_data.get('hash', '0' * 64)
                        else:
                            # Direct blockchain data
                            current_height = data.get('blocks', data.get('total_blocks', 0))
                            latest_hash = data.get('latest_hash', '0' * 64)
                        
                        next_index = current_height + 1
                        
                        print(color_text(f"📊 Blockchain: Height {current_height}", COLORS["G"]))
                        print(color_text(f"🔗 Latest Hash: {latest_hash[:20]}...", COLORS["B"]))
                        
                        # If blockchain is empty, we're mining the genesis block
                        if current_height == 0:
                            previous_hash = "0" * 64
                            print(color_text("🆕 Mining genesis block", COLORS["B"]))
                        else:
                            previous_hash = latest_hash
                            print(color_text(f"⛓️  Linking to block #{current_height}", COLORS["B"]))
                        
                        return next_index, previous_hash
                        
                except Exception as e:
                    print(color_text(f"❌ Endpoint {endpoint} failed: {e}", COLORS["R"]))
                    continue
            
            # If all endpoints fail, try to get blocks directly
            print(color_text("🔄 Trying direct blocks endpoint...", COLORS["O"]))
            blocks_response = requests.get(f"{self.api_base}/api/blockchain/blocks", timeout=10)
            if blocks_response.status_code == 200:
                blocks_data = blocks_response.json()
                blocks = blocks_data.get('blocks', [])
                if blocks:
                    latest_block = blocks[-1]
                    current_height = latest_block.get('index', 0)
                    latest_hash = latest_block.get('hash', '0' * 64)
                    next_index = current_height + 1
                    previous_hash = latest_hash
                    
                    print(color_text(f"📊 Found {len(blocks)} blocks, latest: #{current_height}", COLORS["G"]))
                    return next_index, previous_hash
            
            # Final fallback - check if we can at least connect to the server
            print(color_text("🔄 Testing basic server connectivity...", COLORS["O"]))
            test_response = requests.get(f"{self.api_base}/", timeout=5)
            if test_response.status_code == 200:
                print(color_text("✅ Server is reachable, but blockchain might be empty", COLORS["G"]))
                return 1, "0" * 64  # Start with genesis block
            else:
                print(color_text("❌ Cannot connect to server", COLORS["R"]))
                return None, None
            
        except Exception as e:
            print(color_text(f"❌ Failed to get blockchain info: {e}", COLORS["R"]))
            return None, None

    def debug_blockchain_state(self):
        """Check what's actually in the blockchain"""
        try:
            endpoints = [
                f"{self.api_base}/api/blockchain/blocks?limit=5",
                f"{self.api_base}/blockchain/blocks?limit=5",
                f"{self.api_base}/api/blockchain",
                f"{self.api_base}/blockchain"
            ]
            
            for endpoint in endpoints:
                try:
                    print(color_text(f"🔍 Trying: {endpoint}", COLORS["B"]))
                    response = requests.get(endpoint, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Handle different response formats
                        if isinstance(data, list):
                            blocks = data
                        elif 'blocks' in data:
                            blocks = data['blocks']
                        elif 'status' in data:
                            # Just show status if we can't get blocks
                            status = data['status']
                            print(color_text(f"📊 Blockchain Status: {status.get('blocks', 0)} blocks", COLORS["G"]))
                            return []
                        else:
                            blocks = []
                        
                        print(color_text("\n🔍 Actual Blockchain State:", COLORS["B"]))
                        if not blocks:
                            print(color_text("   Blockchain is EMPTY - no blocks yet", COLORS["O"]))
                        else:
                            for block in blocks[-5:]:  # Show last 5 blocks
                                block_index = block.get('index', 'Unknown')
                                block_hash = block.get('hash', 'N/A')[:20] + '...'
                                print(color_text(f"   Block #{block_index}: {block_hash}", COLORS["G"]))
                        
                        return blocks
                        
                except Exception as e:
                    print(color_text(f"❌ Endpoint {endpoint} failed: {e}", COLORS["R"]))
                    continue
            
            print(color_text("❌ All blockchain endpoints failed", COLORS["R"]))
            return []
                
        except Exception as e:
            print(color_text(f"❌ Blockchain debug failed: {e}", COLORS["R"]))
            return []
    def get_status(self):
        total_bills = len(self.config.get('bills_mined', []))
        total_reward = sum(bill.get('amount', 0) for bill in self.config.get('bills_mined', []))
        total_mining_time = sum(bill.get('mining_time', 0) for bill in self.config.get('bills_mined', []))
        
        return {
            'miner_address': self.config['miner_address'],
            'mempool_size': len(self.mempool),
            'bills_mined': total_bills,
            'total_reward': total_reward,
            'total_mining_time': total_mining_time,
            'auto_mine': self.config.get('auto_mine', False),
            'mining_pool': self.mining_pool,
            'difficulty': self.config.get('difficulty', 4)
        }
    
    def toggle_auto_mine(self):
        self.config['auto_mine'] = not self.config.get('auto_mine', False)
        self.save_config()
        status = "enabled" if self.config['auto_mine'] else "disabled"
        print(color_text(f"🤖 Auto-mining {status}", COLORS["G"]))
        return self.config['auto_mine']
    
    def toggle_mining_pool(self):
        self.config['mining_pool'] = not self.config.get('mining_pool', False)
        self.mining_pool = self.config['mining_pool']
        self.save_config()
        status = "enabled" if self.mining_pool else "disabled"
        print(color_text(f"🔗 Pool mining {status}", COLORS["B"]))
        
        if self.mining_pool:
            self.connect_to_pool()
        
        return self.mining_pool
    
    def set_difficulty(self, difficulty):
        if 1 <= difficulty <= 8:
            self.config['difficulty'] = difficulty
            self.save_config()
            print(color_text(f"🎯 Difficulty set to {difficulty}", COLORS["G"]))
            return True
        else:
            print(color_text("❌ Difficulty must be between 1-8", COLORS["R"]))
            return False
    
    def show_menu(self):
        while self.running:
            print(color_text("\n🌙 Luna Miner", COLORS["I"]))
            print("1. 📊 Status")
            print("2. ⛏️  Mine Now")
            print("3. 🔄 Sync Mempool")
            print("4. 🤖 Toggle Auto-mine")
            print("5. 🔗 Toggle Pool Mining")
            print("6. 🎯 Set Difficulty")
            print("7. 📈 Mining History")
            print("8. 🚪 Exit")
            
            try:
                choice = input(color_text("Choice: ", COLORS["B"])).strip()
                
                if choice == "1":
                    status = self.get_status()
                    print(color_text(f"⛏️  Miner: {status['miner_address']}", COLORS["G"]))
                    print(color_text(f"📊 Mempool: {status['mempool_size']} transactions", COLORS["B"]))
                    print(color_text(f"💰 Bills Mined: {status['bills_mined']}", COLORS["Y"]))
                    print(color_text(f"💎 Total Reward: {status['total_reward']} LUN", COLORS["I"]))
                    print(color_text(f"⏱️  Total Mining Time: {status['total_mining_time']:.1f}s", COLORS["V"]))
                    print(color_text(f"🎯 Difficulty: {status['difficulty']}", COLORS["O"]))
                    print(color_text(f"🤖 Auto-mine: {'On' if status['auto_mine'] else 'Off'}", COLORS["G"]))
                    print(color_text(f"🔗 Pool: {'On' if status['mining_pool'] else 'Off'}", COLORS["B"]))
                    
                elif choice == "2":
                    self.mine_from_mempool()
                    
                elif choice == "3":
                    if self.sync_mempool():
                        print(color_text("✅ Mempool synced", COLORS["G"]))
                    else:
                        print(color_text("❌ Sync failed", COLORS["R"]))
                        
                elif choice == "4":
                    self.toggle_auto_mine()
                    
                elif choice == "5":
                    self.toggle_mining_pool()
                    
                elif choice == "6":
                    try:
                        new_diff = int(input(f"Enter difficulty (1-8, current: {self.config.get('difficulty', 4)}): "))
                        self.set_difficulty(new_diff)
                    except:
                        print(color_text("❌ Invalid difficulty", COLORS["R"]))
                        
                elif choice == "7":
                    bills = self.config.get('bills_mined', [])
                    if not bills:
                        print(color_text("📭 No mining history", COLORS["O"]))
                    else:
                        for i, bill in enumerate(reversed(bills[-10:])):
                            color = [COLORS["R"], COLORS["O"], COLORS["Y"], COLORS["G"], COLORS["B"], COLORS["I"]][i % 6]
                            print(color_text(
                                f"{i+1}. {bill['amount']} LUN - {bill['transactions']} txs - {bill.get('mining_time', 0):.1f}s", 
                                color
                            ))
                            
                elif choice == "8":
                    self.running = False
                    print(color_text("👋 Goodbye!", COLORS["G"]))
                    
            except (KeyboardInterrupt, EOFError):
                self.running = False
                print(color_text("\n👋 Goodbye!", COLORS["G"]))
            except Exception as e:
                print(color_text(f"Error: {e}", COLORS["R"]))

def main():
    node = LunaNode()
    node.show_menu()

if __name__ == "__main__":
    main()