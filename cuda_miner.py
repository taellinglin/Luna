#!/usr/bin/env python3
import requests
import time
import hashlib
import json
import logging
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s [CUDA] %(message)s')
logger = logging.getLogger("cuda_miner")

class BasicMiner:
    def __init__(self, base_url, miner_address):
        self.base_url = base_url
        self.miner_address = miner_address
        self.is_mining = True
        
    def start_mining(self):
        logger.info(f"Starting basic miner: {self.miner_address}")
        while self.is_mining:
            try:
                # Try to mine
                payload = {"miner_address": self.miner_address}
                resp = requests.post(f"{self.base_url}/api/block/mine", json=payload, timeout=30)
                
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("status") == "success" and data.get("block"):
                        block = data["block"]
                        tx_count = len(block.get("transactions", []))
                        logger.info(f"Mined block #{block.get('index')} with {tx_count} transactions!")
                    else:
                        logger.debug(f"No transactions: {data.get('message')}")
                elif resp.status_code == 400:
                    logger.debug("No transactions available")
                else:
                    logger.warning(f"Mining failed: {resp.status_code}")
                    
            except Exception as e:
                logger.error(f"Mining error: {e}")
                
            time.sleep(5)  # Wait before next attempt

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--miner', required=True)
    parser.add_argument('--url', required=True)
    args = parser.parse_args()
    
    miner = BasicMiner(args.url, args.miner)
    try:
        miner.start_mining()
    except KeyboardInterrupt:
        miner.is_mining = False
        print("Miner stopped")
