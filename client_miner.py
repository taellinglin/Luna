# client_miner.py
import requests
import hashlib
import json
import time
import logging

class ClientMiner:
    def __init__(self, base_url, miner_address):
        self.base_url = base_url
        self.miner_address = miner_address
        self.is_mining = False
        
    def get_mining_work(self):
        """Get mining work from server"""
        try:
            response = requests.get(f"{self.base_url}/api/mining/work", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    return data["mining_work"]
            return None
        except Exception as e:
            logging.error(f"Error getting mining work: {e}")
            return None
    
    def mine_block(self, mining_work):
        """Perform proof of work on the given work"""
        target = mining_work["target"]
        nonce = 0
        start_time = time.time()
        
        while self.is_mining:
            # Create block candidate
            block_candidate = {
                "index": mining_work["index"],
                "timestamp": mining_work["timestamp"],
                "transactions": mining_work["transactions"],
                "previous_hash": mining_work["previous_hash"],
                "nonce": nonce,
                "miner": self.miner_address,
                "difficulty": mining_work["difficulty"],
                "hash": ""
            }
            
            # Calculate hash
            calculated_hash = self.calculate_block_hash(block_candidate)
            
            # Check if hash meets target
            if calculated_hash.startswith(target):
                block_candidate["hash"] = calculated_hash
                mining_time = time.time() - start_time
                block_candidate["mining_time"] = mining_time
                return block_candidate
            
            nonce += 1
            
            # Safety check
            if nonce % 100000 == 0:
                logging.info(f"Tried {nonce} nonces...")
            if nonce > 10000000:  # 10 million nonce limit
                break
        
        return None
    
    def calculate_block_hash(self, block):
        """Calculate block hash (must match server's method)"""
        # This must EXACTLY match your server's calculate_block_hash method
        index = int(block["index"])
        previous_hash = block["previous_hash"]
        timestamp = int(block["timestamp"])
        transactions = block["transactions"]
        nonce = int(block["nonce"])
        difficulty = block.get("difficulty")
        
        # Sort transactions for consistency
        if transactions:
            sorted_transactions = sorted(transactions, key=lambda x: x.get('hash', ''))
            transactions_string = json.dumps(sorted_transactions, sort_keys=True, separators=(',', ':'))
        else:
            transactions_string = "[]"
        
        # Build block data (must match server exactly)
        block_data = {
            'index': index,
            'previous_hash': previous_hash,
            'timestamp': timestamp,
            'transactions': transactions_string,
            'nonce': nonce
        }
        
        if difficulty is not None:
            block_data['difficulty'] = int(difficulty)
        
        block_string = json.dumps(block_data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def submit_block(self, mined_block):
        """Submit mined block to server"""
        try:
            submission_data = {
                "block": mined_block,
                "miner_address": self.miner_address,
                "nonce": mined_block["nonce"],
                "hash": mined_block["hash"],
                "difficulty": mined_block["difficulty"]
            }
            
            response = requests.post(
                f"{self.base_url}/api/block/submit",
                json=submission_data,
                timeout=30
            )
            
            return response.json()
            
        except Exception as e:
            logging.error(f"Error submitting block: {e}")
            return {"status": "error", "message": str(e)}
    
    def start_mining(self):
        """Main mining loop"""
        self.is_mining = True
        consecutive_failures = 0
        
        logging.info(f"Starting client miner: {self.miner_address}")
        
        while self.is_mining:
            try:
                # Get mining work
                mining_work = self.get_mining_work()
                if not mining_work:
                    consecutive_failures += 1
                    wait_time = min(consecutive_failures * 5, 60)
                    logging.info(f"No mining work available. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                
                consecutive_failures = 0
                
                logging.info(f"⛏️ Mining block #{mining_work['index']} with {len(mining_work['transactions'])} transactions")
                
                # Mine the block
                mined_block = self.mine_block(mining_work)
                
                if mined_block:
                    # Submit to server
                    result = self.submit_block(mined_block)
                    
                    if result.get("status") == "success":
                        logging.info(f"✅ Successfully mined block #{mined_block['index']}!")
                        logging.info(f"   Reward: {result.get('reward_amount', 0)}")
                        logging.info(f"   Nonce: {mined_block['nonce']}")
                        logging.info(f"   Hash: {mined_block['hash'][:16]}...")
                    else:
                        logging.error(f"❌ Block rejected: {result.get('message')}")
                else:
                    logging.info("❌ Failed to find valid nonce for current work")
                    # Get new work
                    time.sleep(1)
                
            except Exception as e:
                logging.error(f"💥 Mining error: {e}")
                consecutive_failures += 1
                time.sleep(10)
    
    def stop_mining(self):
        self.is_mining = False