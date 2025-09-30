#!/usr/bin/env python3
"""
luna_sim.py

Enhanced Luna Coin blockchain simulator with:
- Wallet-to-wallet transfers using the /api/transaction/broadcast endpoint
- Reward transaction creation using /api/transaction/reward endpoint
- Mining of all transaction types
- Comprehensive transaction monitoring

Usage:
  python luna_sim.py
"""

import requests
import threading
import time
import logging
import subprocess
import sys
import os
import random
import json
import hashlib
import secrets
from typing import List, Dict, Optional

# -----------------------
# CONFIG
# -----------------------
BASE_URL = "https://bank.linglin.art/"
NUM_CUDA_MINERS = 310
NUM_CPU_MINERS = 310
MINING_CHECK_INTERVAL = 0.1
LOG_LEVEL = logging.INFO

# Enhanced wallet configuration
NUM_WALLETS = 100
NETWORK_DATA_DIR = "network-data"
WALLET_FILE = f"{NETWORK_DATA_DIR}/miner_wallets.json"

# Transaction simulation settings
TRANSFER_INTERVAL = 0.5  # seconds between transfer simulations
MIN_TRANSFER_AMOUNT = 1.0
MAX_TRANSFER_AMOUNT = 10.0
REWARD_INTERVAL = 30  # seconds between reward simulations
REWARD_AMOUNT = 1
# -----------------------

# HTTP endpoints from app.py
ENDPOINT_MINE = f"{BASE_URL}/api/block/mine"
ENDPOINT_STATUS = f"{BASE_URL}/api/blockchain/status"
ENDPOINT_MEMPOOL = f"{BASE_URL}/mempool"
ENDPOINT_BROADCAST = f"{BASE_URL}/api/transaction/broadcast"  # For sending transfers
ENDPOINT_REWARD = f"{BASE_URL}/api/transaction/reward"  # For creating rewards
ENDPOINT_BLOCKCHAIN = f"{BASE_URL}/blockchain"

# Logging
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("luna_sim")

class EnhancedWalletManager:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.wallets = []
        self.current_wallet_index = 0
        self.transfer_counter = 0
        self.reward_counter = 0
        
    def generate_wallets(self, num_wallets: int) -> List[Dict]:
        """Generate wallets with enhanced capabilities for transfers and rewards"""
        os.makedirs(NETWORK_DATA_DIR, exist_ok=True)
        
        if os.path.exists(WALLET_FILE):
            try:
                with open(WALLET_FILE, 'r') as f:
                    self.wallets = json.load(f)
                logger.info(f"✅ Loaded {len(self.wallets)} existing wallets from {WALLET_FILE}")
                # Fix any missing fields in existing wallets
                self.fix_wallet_fields()
                return self.wallets
            except Exception as e:
                logger.warning(f"⚠️ Could not load existing wallets: {e}")
        
        for i in range(num_wallets):
            wallet = self._generate_enhanced_wallet(i)
            self.wallets.append(wallet)
            
        self._save_wallets()
        logger.info(f"✅ Generated and saved {len(self.wallets)} enhanced wallets")
        
        return self.wallets
    
    def _generate_enhanced_wallet(self, wallet_id: int) -> Dict:
        """Generate a wallet with transfer and reward capabilities"""
        private_key = secrets.token_hex(32)
        address = hashlib.sha256(private_key.encode()).hexdigest()[:40]
        
        wallet = {
            "id": wallet_id,
            "name": f"miner_wallet_{wallet_id:02d}",
            "address": address,
            "private_key": private_key,
            "created_at": time.time(),
            "balance": 1000.0,  # Starting balance for simulation
            "mined_blocks": 0,
            "sent_transactions": 0,  # Initialize all stats to 0
            "received_transactions": 0,
            "total_sent": 0.0,
            "total_received": 0.0
        }
        
        individual_wallet_file = f"{NETWORK_DATA_DIR}/wallet_{wallet_id:02d}.json"
        with open(individual_wallet_file, 'w') as f:
            json.dump(wallet, f, indent=2)
            
        return wallet
    
    def _save_wallets(self):
        """Save all wallets to file"""
        with open(WALLET_FILE, 'w') as f:
            json.dump(self.wallets, f, indent=2)
    
    def get_next_miner_address(self) -> str:
        """Get the next wallet address for mining"""
        if not self.wallets:
            return "default_miner"
            
        address = self.wallets[self.current_wallet_index]["address"]
        self.current_wallet_index = (self.current_wallet_index + 1) % len(self.wallets)
        return address
    
    def get_random_wallet(self, exclude_address: str = None) -> Optional[Dict]:
        """Get a random wallet, optionally excluding one"""
        if not self.wallets:
            return None
            
        available_wallets = [w for w in self.wallets if w["address"] != exclude_address]
        if not available_wallets:
            return None
            
        return random.choice(available_wallets)
    
    # In the EnhancedWalletManager class, update the create_transfer_transaction method:

    def create_transfer_transaction(self, from_wallet: Dict, to_address: str, amount: float) -> Dict:
        """Fixed transfer creation with proper validation"""
        self.transfer_counter += 1
        
        # Ensure amount is valid
        if amount <= 0 or amount > from_wallet.get("balance", 0):
            logger.error(f"❌ Invalid transfer amount: {amount}, balance: {from_wallet.get('balance', 0)}")
            return None
        
        # Initialize wallet stats if they don't exist
        if "sent_transactions" not in from_wallet:
            from_wallet["sent_transactions"] = 0
            from_wallet["total_sent"] = 0.0
        
        # Create transfer with proper structure
        transfer_tx = {
            "type": "transfer",
            "from": from_wallet["address"],
            "to": to_address,
            "amount": float(amount),
            "timestamp": int(time.time()),  # Use integer timestamp
            "signature": f"sim_signature_{self.transfer_counter:06d}_{secrets.token_hex(16)}",
            "public_key": f"sim_pubkey_{from_wallet['address']}",
            "hash": ""
        }
        
        # Calculate hash (match your blockchain's method exactly)
        tx_string = json.dumps({
            "type": transfer_tx["type"],
            "from": transfer_tx["from"],
            "to": transfer_tx["to"], 
            "amount": transfer_tx["amount"],
            "timestamp": transfer_tx["timestamp"],
            "signature": transfer_tx["signature"]
        }, sort_keys=True)
        
        transfer_tx["hash"] = hashlib.sha256(tx_string.encode()).hexdigest()
        
        logger.info(f"💸 Created transfer: {amount} from {from_wallet['address'][:8]} to {to_address[:8]}")
        return transfer_tx
    def create_reward_transaction(self, to_address: str, amount: float, block_height: int) -> Dict:
        """Create a reward transaction for broadcasting"""
        self.reward_counter += 1
        
        reward_tx = {
            "type": "reward",
            "to": to_address,
            "amount": amount,
            "timestamp": time.time(),
            "block_height": block_height,
            "description": f"Simulation reward #{self.reward_counter}",
            "hash": ""  # Will be calculated by the server
        }
        
        # Update recipient wallet with proper field initialization
        for wallet in self.wallets:
            if wallet["address"] == to_address:
                wallet["balance"] = wallet.get("balance", 0) + amount
                wallet["received_transactions"] = wallet.get("received_transactions", 0) + 1
                wallet["total_received"] = wallet.get("total_received", 0.0) + amount
                break
        
        self._save_wallets()
        
        return reward_tx
    
    def broadcast_transaction(self, transaction: Dict) -> bool:
        """Broadcast a transaction to the mempool"""
        try:
            logger.info(f"📨 Broadcasting {transaction['type']} transaction: {transaction.get('hash', 'unknown')[:16]}...")
            
            response = requests.post(
                ENDPOINT_BROADCAST,
                json=transaction,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    logger.info(f"✅ {transaction['type'].title()} transaction broadcast successful")
                    return True
                else:
                    logger.warning(f"⚠️ Broadcast failed: {result.get('message', 'Unknown error')}")
            else:
                logger.error(f"❌ Broadcast HTTP error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"💥 Broadcast error: {e}")
            
        return False
    
    def create_reward_via_api(self, to_address: str, amount: float, block_height: int) -> bool:
        """Create a reward transaction using the API endpoint"""
        try:
            reward_data = {
                "to": to_address,
                "amount": amount,
                "description": f"Automated simulation reward at block {block_height}",
                "block_height": block_height
            }
            
            logger.info(f"🎁 Creating reward via API: {amount} to {to_address}")
            
            response = requests.post(
                ENDPOINT_REWARD,
                json=reward_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    logger.info(f"✅ Reward creation successful: {result.get('transaction_hash', 'unknown')}")
                    
                    # Update local wallet balance with proper field initialization
                    for wallet in self.wallets:
                        if wallet["address"] == to_address:
                            wallet["balance"] = wallet.get("balance", 0) + amount
                            wallet["received_transactions"] = wallet.get("received_transactions", 0) + 1
                            wallet["total_received"] = wallet.get("total_received", 0.0) + amount
                            break
                    
                    self._save_wallets()
                    
                    return True
                else:
                    logger.warning(f"⚠️ Reward creation failed: {result.get('message', 'Unknown error')}")
            else:
                logger.error(f"❌ Reward API HTTP error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"💥 Reward creation error: {e}")
            
        return False
        
    def update_wallet_balance(self, wallet_address: str, amount: float):
        """Update wallet balance when rewards are received"""
        for wallet in self.wallets:
            if wallet["address"] == wallet_address:
                wallet["balance"] = wallet.get("balance", 0) + amount
                wallet["mined_blocks"] = wallet.get("mined_blocks", 0) + 1
                break
        
        self._save_wallets()
    
    def get_wallet_stats(self):
        """Get enhanced statistics about all wallets"""
        total_balance = sum(wallet.get("balance", 0) for wallet in self.wallets)
        total_mined = sum(wallet.get("mined_blocks", 0) for wallet in self.wallets)
        total_sent = sum(wallet.get("total_sent", 0) for wallet in self.wallets)
        total_received = sum(wallet.get("total_received", 0) for wallet in self.wallets)
        
        return {
            "total_wallets": len(self.wallets),
            "total_balance": total_balance,
            "total_mined_blocks": total_mined,
            "total_sent_amount": total_sent,
            "total_received_amount": total_received,
            "total_transfers": self.transfer_counter,
            "total_rewards": self.reward_counter,
            "wallets": self.wallets
        }

class TransferSimulator:
    def __init__(self, wallet_manager: EnhancedWalletManager):
        self.wallet_manager = wallet_manager
        self.is_running = False
        self.transfer_count = 0
        
    def start_transfer_simulation(self, interval: float = TRANSFER_INTERVAL):
        """Start simulating wallet-to-wallet transfers"""
        self.is_running = True
        
        def transfer_loop(self):
            logger.info(f"🔄 Starting transfer simulation (interval: {interval}s)")
            
            while self.is_running:
                try:
                    # Wait for interval
                    time.sleep(interval)
                    
                    # Get random sender and receiver
                    sender = self.wallet_manager.get_random_wallet()
                    if not sender:
                        continue
                        
                    receiver = self.wallet_manager.get_random_wallet(exclude_address=sender["address"])
                    if not receiver:
                        continue
                    
                    # Check sender balance
                    if sender["balance"] < MIN_TRANSFER_AMOUNT:
                        logger.debug(f"💰 Insufficient balance for transfer from {sender['address'][:8]}")
                        continue
                    
                    # Random amount
                    amount = round(random.uniform(MIN_TRANSFER_AMOUNT, min(MAX_TRANSFER_AMOUNT, sender["balance"])), 2)
                    
                    # Create and broadcast transfer
                    transfer_tx = self.wallet_manager.create_transfer_transaction(sender, receiver["address"], amount)
                    
                    if transfer_tx and self.wallet_manager.broadcast_transaction(transfer_tx):
                        # Update wallet balances only if broadcast succeeds
                        sender["balance"] -= amount
                        sender["sent_transactions"] = sender.get("sent_transactions", 0) + 1
                        sender["total_sent"] = sender.get("total_sent", 0) + amount
                        
                        receiver["balance"] += amount
                        receiver["received_transactions"] = receiver.get("received_transactions", 0) + 1
                        receiver["total_received"] = receiver.get("total_received", 0) + amount
                        
                        self.transfer_count += 1
                        logger.info(f"💸 Transfer #{self.transfer_count}: {amount} from {sender['address'][:8]} to {receiver['address'][:8]}")
                        
                        # Save updated wallets
                        self.wallet_manager._save_wallets()
                    else:
                        logger.warning(f"❌ Transfer broadcast failed, no balance changes made")
                        
                except Exception as e:
                    logger.error(f"💥 Transfer simulation error: {e}")
                    time.sleep(5)  # Wait before retrying
        
        t = threading.Thread(target=transfer_loop(self), daemon=True)
        t.start()
        return t
    
    def stop_transfer_simulation(self):
        self.is_running = False

class RewardSimulator:
    def __init__(self, wallet_manager: EnhancedWalletManager):
        self.wallet_manager = wallet_manager
        self.is_running = False
        self.reward_count = 0
        
    def start_reward_simulation(self, interval: float = REWARD_INTERVAL):
        """Start simulating reward transactions"""
        self.is_running = True
        
        def reward_loop(self):
            logger.info(f"🎁 Starting reward simulation (interval: {interval}s)")
    
            while self.is_running:
                try:
                    # Wait for interval
                    time.sleep(interval)
                    
                    # Get random recipient
                    recipient = self.wallet_manager.get_random_wallet()
                    if not recipient:
                        continue
                    
                    # Get current blockchain height for the reward
                    try:
                        status_resp = requests.get(ENDPOINT_STATUS, timeout=5)
                        if status_resp.status_code == 200:
                            status_data = status_resp.json()
                            block_height = status_data.get('blockchain_height', 0) + 1
                        else:
                            block_height = self.reward_count + 1
                    except:
                        block_height = self.reward_count + 1
                    
                    # Create reward using API endpoint
                    if self.wallet_manager.create_reward_via_api(recipient["address"], REWARD_AMOUNT, block_height):
                        self.reward_count += 1
                        logger.info(f"⭐ Reward #{self.reward_count}: {REWARD_AMOUNT} to {recipient['address'][:8]} (block {block_height})")
                    else:
                        # Alternative: create and broadcast reward transaction directly
                        reward_tx = self.wallet_manager.create_reward_transaction(recipient["address"], REWARD_AMOUNT, block_height)
                        if self.wallet_manager.broadcast_transaction(reward_tx):
                            self.reward_count += 1
                            logger.info(f"⭐ Reward #{self.reward_count} (direct): {REWARD_AMOUNT} to {recipient['address'][:8]}")
                        else:
                            # Revert wallet changes if broadcast failed with proper field handling
                            for wallet in self.wallet_manager.wallets:
                                if wallet["address"] == recipient["address"]:
                                    wallet["balance"] = wallet.get("balance", 0) - REWARD_AMOUNT
                                    wallet["received_transactions"] = max(0, wallet.get("received_transactions", 0) - 1)
                                    wallet["total_received"] = max(0.0, wallet.get("total_received", 0.0) - REWARD_AMOUNT)
                                    break
                            
                            logger.warning("❌ Reward broadcast failed, reverted wallet changes")
                            
                except Exception as e:
                    logger.error(f"💥 Reward simulation error: {e}")
                    time.sleep(10)  # Wait before retrying
        
        t = threading.Thread(target=reward_loop(self), daemon=True)
        t.start()
        return t
    
    def stop_reward_simulation(self):
        self.is_running = False

class CUDAMinerManager:
    def __init__(self, base_url: str, wallet_manager: EnhancedWalletManager, num_miners: int = 3):
        self.base_url = base_url
        self.wallet_manager = wallet_manager
        self.num_miners = num_miners
        self.processes = []
        self.is_running = False
        
    def start_miners(self):
        """Start CUDA miner processes"""
        self.is_running = True
        logger.info(f"🚀 Starting {self.num_miners} CUDA miner processes...")
        
        for i in range(self.num_miners):
            miner_addr = self.wallet_manager.get_next_miner_address()
            self._start_miner_process(i, miner_addr)
            
    def _start_miner_process(self, miner_id: int, miner_address: str):
        """Start a single CUDA miner as a subprocess"""
        try:
            if not os.path.exists("cuda_miner.py"):
                logger.error("❌ cuda_miner.py not found! Creating enhanced version...")
                self._create_enhanced_cuda_miner()
            
            cmd = [
                sys.executable, "./cuda_miner.py",
                "--miner", miner_address,
                "--url", self.base_url.rstrip('/')
            ]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )
            
            self.processes.append((miner_id, process, miner_address))
            logger.info(f"✅ Started CUDA miner {miner_id}: {miner_address}")
            
            threading.Thread(
                target=self._monitor_miner_output,
                args=(miner_id, process, miner_address),
                daemon=True
            ).start()
            
        except Exception as e:
            logger.error(f"❌ Failed to start CUDA miner {miner_id}: {e}")
    
    def _monitor_miner_output(self, miner_id: int, process, miner_address: str):
        """Monitor miner process output"""
        try:
            while self.is_running and process.poll() is None:
                output = process.stdout.readline()
                if output:
                    logger.info(f"⛏️ CUDA-{miner_id}: {output.strip()}")
                
                error = process.stderr.readline()
                if error:
                    logger.error(f"💥 CUDA-{miner_id}: {error.strip()}")
                    
                time.sleep(0.1)
                
            return_code = process.poll()
            if return_code is not None and return_code != 0:
                logger.warning(f"⚠️ CUDA miner {miner_id} exited with code {return_code}")
                
        except Exception as e:
            logger.error(f"Error monitoring CUDA miner {miner_id}: {e}")
    
    def _create_enhanced_cuda_miner(self):
        """Create an enhanced CUDA miner that handles all transaction types"""
        enhanced_miner_code = '''#!/usr/bin/env python3
import requests
import time
import logging
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s [CUDA] %(message)s')
logger = logging.getLogger("cuda_miner")

class EnhancedMiner:
    def __init__(self, base_url, miner_address):
        self.base_url = base_url
        self.miner_address = miner_address
        self.is_mining = True
        
    def start_mining(self):
        logger.info(f"Starting enhanced miner for: {self.miner_address}")
        consecutive_empty = 0
        
        while self.is_mining:
            try:
                # Try to mine all transaction types
                payload = {"miner_address": self.miner_address, "async": False}
                resp = requests.post(f"{self.base_url}/api/block/mine", json=payload, timeout=30)
                
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("status") == "success" and data.get("block"):
                        block = data["block"]
                        tx_count = len(block.get("transactions", []))
                        
                        # Detailed transaction type analysis
                        genesis_count = 0
                        transfer_count = 0
                        reward_count = 0
                        other_count = 0
                        
                        for tx in block.get("transactions", []):
                            tx_type = tx.get("type", "").lower()
                            if "genesis" in tx_type or "gtx" in tx_type:
                                genesis_count += 1
                            elif "transfer" in tx_type:
                                transfer_count += 1
                            elif "reward" in tx_type:
                                reward_count += 1
                            else:
                                other_count += 1
                        
                        logger.info(f"✅ Mined block #{block.get('index')} with {tx_count} tx (G:{genesis_count} T:{transfer_count} R:{reward_count} O:{other_count})")
                        consecutive_empty = 0
                    else:
                        consecutive_empty += 1
                        if consecutive_empty % 10 == 0:
                            logger.debug(f"No transactions: {data.get('message')}")
                elif resp.status_code == 400:
                    consecutive_empty += 1
                    if consecutive_empty % 10 == 0:
                        logger.debug(f"No transactions available")
                elif resp.status_code == 500:
                    consecutive_empty += 1
                    if consecutive_empty % 5 == 0:
                        logger.warning(f"Server error: {resp.status_code}")
                    time.sleep(10)
                else:
                    logger.warning(f"Mining failed: {resp.status_code}")
                    consecutive_empty += 1
                    
                wait_time = max(3.0, min(consecutive_empty * 1.0, 15.0))
                time.sleep(wait_time)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Network error: {e}")
                time.sleep(10)
            except Exception as e:
                logger.error(f"Mining error: {e}")
                time.sleep(10)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--miner', required=True)
    parser.add_argument('--url', required=True)
    args = parser.parse_args()
    
    miner = EnhancedMiner(args.url, args.miner)
    try:
        miner.start_mining()
    except KeyboardInterrupt:
        miner.is_mining = False
        print("Miner stopped")
'''
        with open("cuda_miner.py", "w") as f:
            f.write(enhanced_miner_code)
        logger.info("✅ Created enhanced cuda_miner.py")
    
    def stop_miners(self):
        """Stop all CUDA miner processes"""
        self.is_running = False
        logger.info("🛑 Stopping CUDA miners...")
        
        for miner_id, process, address in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
                logger.info(f"✅ Stopped CUDA miner {miner_id}")
            except subprocess.TimeoutExpired:
                process.kill()
                logger.warning(f"⚠️ Force killed CUDA miner {miner_id}")
            except Exception as e:
                logger.error(f"❌ Error stopping CUDA miner {miner_id}: {e}")

class CPUMiner:
    def __init__(self, base_url: str, wallet_manager: EnhancedWalletManager, miner_address: str):
        self.base_url = base_url
        self.wallet_manager = wallet_manager
        self.miner_address = miner_address
        self.is_mining = False
        
    def start_mining(self):
        """CPU mining loop"""
        self.is_mining = True
        logger.info(f"💻 Starting CPU miner: {self.miner_address}")
        
        consecutive_empty = 0
        
        while self.is_mining:
            try:
                payload = {"miner_address": self.miner_address}
                resp = requests.post(f"{self.base_url}/api/block/mine", json=payload, timeout=30)
                
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("status") == "success" and data.get("block"):
                        block = data["block"]
                        tx_count = len(block.get("transactions", []))
                        
                        # Transaction type analysis
                        genesis_count = 0
                        transfer_count = 0
                        reward_count = 0
                        other_count = 0
                        
                        for tx in block.get("transactions", []):
                            tx_type = tx.get("type", "").lower()
                            if "genesis" in tx_type or "gtx" in tx_type:
                                genesis_count += 1
                            elif "transfer" in tx_type:
                                transfer_count += 1
                            elif "reward" in tx_type:
                                reward_count += 1
                            else:
                                other_count += 1
                        
                        logger.info(f"✅ CPU mined block #{block.get('index')} with {tx_count} tx (G:{genesis_count} T:{transfer_count} R:{reward_count} O:{other_count})")
                        
                        # Update wallet with mining reward
                        reward_amount = 1.0
                        self.wallet_manager.update_wallet_balance(self.miner_address, reward_amount)
                        
                        consecutive_empty = 0
                    else:
                        consecutive_empty += 1
                else:
                    consecutive_empty += 1
                
                wait_time = max(3.0, min(consecutive_empty * 1.5, 20.0))
                time.sleep(wait_time)
                
            except Exception as e:
                logger.error(f"💥 CPU miner error: {e}")
                consecutive_empty += 1
                time.sleep(10)
    
    def stop_mining(self):
        self.is_mining = False

class EnhancedMempoolMonitor:
    def __init__(self, base_url: str, wallet_manager: EnhancedWalletManager):
        self.base_url = base_url
        self.wallet_manager = wallet_manager
        self.stop_event = threading.Event()
        
    def start_monitoring(self, interval=15.0):
        """Enhanced mempool monitoring with transaction analytics"""
        def monitor_loop():
            logger.info("📊 Enhanced mempool monitor started")
            while not self.stop_event.is_set():
                try:
                    # Blockchain status
                    status_resp = requests.get(f"{self.base_url}/api/blockchain/status", timeout=10)
                    if status_resp.status_code == 200:
                        status_data = status_resp.json()
                        height = status_data.get('blockchain_height', 0)
                        mempool_size = status_data.get('mempool_size', 0)
                        
                        logger.info(f"📈 Chain height: {height}, Mempool: {mempool_size}")
                    
                    # Mempool composition
                    mempool_resp = requests.get(f"{self.base_url}/mempool", timeout=10)
                    if mempool_resp.status_code == 200:
                        mempool = mempool_resp.json()
                        
                        genesis_count = 0
                        transfer_count = 0
                        reward_count = 0
                        other_count = 0
                        
                        for tx in mempool:
                            tx_type = tx.get("type", "").lower()
                            if "genesis" in tx_type or "gtx" in tx_type:
                                genesis_count += 1
                            elif "transfer" in tx_type:
                                transfer_count += 1
                            elif "reward" in tx_type:
                                reward_count += 1
                            else:
                                other_count += 1
                        
                        total_tx = len(mempool)
                        if total_tx > 0:
                            logger.info(f"📦 Mempool: {total_tx} tx (Genesis: {genesis_count}, Transfers: {transfer_count}, Rewards: {reward_count}, Other: {other_count})")
                        else:
                            logger.debug("📭 Mempool is empty")
                    
                    # Enhanced wallet statistics
                    wallet_stats = self.wallet_manager.get_wallet_stats()
                    logger.info(f"💰 Enhanced Wallet Stats: {wallet_stats['total_wallets']} wallets, Balance: {wallet_stats['total_balance']:.2f}, Transfers: {wallet_stats['total_transfers']}, Rewards: {wallet_stats['total_rewards']}")
                            
                except Exception as e:
                    logger.error(f"📊 Monitoring error: {e}")
                
                time.sleep(interval)
        
        t = threading.Thread(target=monitor_loop, daemon=True)
        t.start()
        return t
    
    def stop_monitoring(self):
        self.stop_event.set()

class LunaSimulator:
    def __init__(self, num_cuda_miners=NUM_CUDA_MINERS, num_cpu_miners=NUM_CPU_MINERS):
        self.stop_event = threading.Event()
        self.num_cuda_miners = num_cuda_miners
        self.num_cpu_miners = num_cpu_miners
        
        # Initialize enhanced wallet manager
        self.wallet_manager = EnhancedWalletManager(BASE_URL)
        
        # Initialize all simulators and managers
        self.transfer_simulator = TransferSimulator(self.wallet_manager)
        self.reward_simulator = RewardSimulator(self.wallet_manager)
        self.cuda_manager = CUDAMinerManager(BASE_URL, self.wallet_manager, num_cuda_miners)
        self.cpu_miners = []
        self.monitor = EnhancedMempoolMonitor(BASE_URL, self.wallet_manager)
        self.threads = []
        
    def start_cpu_miners(self):
        """Start CPU miners"""
        for i in range(self.num_cpu_miners):
            miner_addr = self.wallet_manager.get_next_miner_address()
            miner = CPUMiner(BASE_URL, self.wallet_manager, miner_addr)
            
            def miner_worker(miner_instance):
                miner_instance.start_mining()
            
            t = threading.Thread(target=miner_worker, args=(miner,), daemon=True)
            t.start()
            self.cpu_miners.append(miner)
            self.threads.append(t)
            
        logger.info(f"💻 Started {self.num_cpu_miners} CPU miners")
    
    def run(self):
        logger.info("🚀 Starting Enhanced Luna Coin Simulator")
        logger.info("💸 Features: Wallet transfers + Reward transactions + Mining")
        
        # Generate enhanced wallets
        logger.info("👛 Generating enhanced wallets with transfer capabilities...")
        self.wallet_manager.generate_wallets(NUM_WALLETS)
        
        # Test connection
        try:
            resp = requests.get(f"{BASE_URL}/api/blockchain/status", timeout=10)
            if resp.status_code == 200:
                logger.info("✅ Connected to blockchain server")
                data = resp.json()
                logger.info(f"📋 Initial state: Height {data.get('blockchain_height')}, Mempool: {data.get('mempool_size')}")
            else:
                logger.warning(f"⚠️ Server response: {resp.status_code}")
        except Exception as e:
            logger.error(f"❌ Cannot connect to {BASE_URL}: {e}")
            return
        
        # Start monitoring
        logger.info("📊 Starting enhanced mempool monitor...")
        self.monitor.start_monitoring(interval=15.0)
        
        # Start transfer simulation
        logger.info("💸 Starting transfer simulation...")
        self.transfer_simulator.start_transfer_simulation(interval=TRANSFER_INTERVAL)
        time.sleep(2)
        
        # Start reward simulation  
        logger.info("🎁 Starting reward simulation...")
        self.reward_simulator.start_reward_simulation(interval=REWARD_INTERVAL)
        time.sleep(2)
        
        # Start CPU miners
        logger.info("💻 Starting CPU miners...")
        self.start_cpu_miners()
        time.sleep(2)
        
        # Start CUDA miners
        logger.info("🎯 Starting CUDA miners...")
        self.cuda_manager.start_miners()
        
        logger.info("🎬 Enhanced Luna Simulator fully operational!")
        logger.info("💸 Automatic wallet-to-wallet transfers running")
        logger.info("🎁 Automatic reward creation running") 
        logger.info("⛏️ Mining all transaction types")
        logger.info(f"📁 Wallet data in: {NETWORK_DATA_DIR}/")

        try:
            while not self.stop_event.is_set():
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt: stopping simulator")
        
        finally:
            self.stop_event.set()
            logger.info("🛑 Shutting down Enhanced Luna Simulator...")
            
            # Stop all components
            self.monitor.stop_monitoring()
            self.transfer_simulator.stop_transfer_simulation()
            self.reward_simulator.stop_reward_simulation()
            self.cuda_manager.stop_miners()
            
            for miner in self.cpu_miners:
                miner.stop_mining()
            
            # Final enhanced stats
            wallet_stats = self.wallet_manager.get_wallet_stats()
            logger.info(f"💰 Final Enhanced Stats:")
            logger.info(f"   Wallets: {wallet_stats['total_wallets']}")
            logger.info(f"   Total Balance: {wallet_stats['total_balance']:.2f}")
            logger.info(f"   Total Transfers: {wallet_stats['total_transfers']}")
            logger.info(f"   Total Rewards: {wallet_stats['total_rewards']}")
            logger.info(f"   Total Mined Blocks: {wallet_stats['total_mined_blocks']}")
            
            time.sleep(2)
            logger.info("✅ Enhanced Luna Simulator stopped successfully")

if __name__ == "__main__":
    logger.info("🎮 Starting Enhanced Luna Coin Simulator with Transfers & Rewards")
    
    simulator = LunaSimulator(
        num_cuda_miners=NUM_CUDA_MINERS,
        num_cpu_miners=NUM_CPU_MINERS
    )
    
    simulator.run()
    
    logger.info("🏁 Enhanced Luna Simulator finished.")