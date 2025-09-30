# manual_debug.py
#!/usr/bin/env python3
"""
Manual debugging script for Luna Node and Wallet
"""

import os
import json
import time
from luna_wallet import LunaWallet, DataManager


def debug_data_files():
    """Debug data files structure"""
    print("=== DATA FILES DEBUG ===")

    data_dir = DataManager.get_data_dir()
    print(f"Data directory: {data_dir}")
    print(f"Exists: {os.path.exists(data_dir)}")

    if os.path.exists(data_dir):
        files = os.listdir(data_dir)
        print(f"Files in data directory ({len(files)}):")
        for file in sorted(files):
            file_path = os.path.join(data_dir, file)
            size = os.path.getsize(file_path) if os.path.isfile(file_path) else 0
            print(f"  {file} ({size} bytes)")

            # Show content of small JSON files
            if file.endswith(".json") and size < 10000:
                try:
                    with open(file_path, "r") as f:
                        content = json.load(f)
                    print(f"    Type: {type(content)}")
                    if isinstance(content, dict):
                        print(f"    Keys: {list(content.keys())}")
                    elif isinstance(content, list):
                        print(f"    Length: {len(content)}")
                except:
                    print("    Could not parse JSON")


def debug_blockchain_transactions():
    """Debug blockchain transaction parsing"""
    print("\n=== BLOCKCHAIN TRANSACTIONS DEBUG ===")

    wallet = LunaWallet()
    blockchain_data = wallet.get_blockchain_data()

    if not blockchain_data:
        print("No blockchain data found")
        return

    print(f"Blockchain data type: {type(blockchain_data)}")

    total_transactions = 0
    address_transactions = {}

    # Parse all blocks
    for block_index, block in enumerate(blockchain_data):
        if not isinstance(block, dict):
            continue

        # Get transactions from various possible field names
        transactions = block.get("transactions", [])
        if not transactions:
            transactions = block.get("data", [])

        if not isinstance(transactions, list):
            continue

        print(f"Block {block_index}: {len(transactions)} transactions")
        total_transactions += len(transactions)

        # Analyze transactions
        for tx in transactions:
            if not isinstance(tx, dict):
                continue

            # Find addresses in transaction
            from_addr = tx.get("from") or tx.get("sender") or tx.get("from_address")
            to_addr = tx.get("to") or tx.get("receiver") or tx.get("to_address")

            if from_addr:
                address_transactions[from_addr] = (
                    address_transactions.get(from_addr, 0) + 1
                )
            if to_addr:
                address_transactions[to_addr] = address_transactions.get(to_addr, 0) + 1

    print(f"\nTotal transactions in blockchain: {total_transactions}")
    print(f"Unique addresses found: {len(address_transactions)}")

    # Show top addresses
    sorted_addresses = sorted(
        address_transactions.items(), key=lambda x: x[1], reverse=True
    )[:10]
    print("\nTop addresses by transaction count:")
    for addr, count in sorted_addresses:
        print(f"  {addr}: {count} transactions")


def debug_wallet_sync():
    """Debug wallet synchronization process"""
    print("\n=== WALLET SYNC DEBUG ===")

    wallet = LunaWallet()

    # Sync and show results
    print("Syncing wallet with blockchain...")
    start_time = time.time()
    sync_result = wallet.sync_with_node()
    sync_time = time.time() - start_time

    print(f"Sync result: {sync_result}")
    print(f"Sync time: {sync_time:.2f} seconds")

    if wallet.addresses:
        for i, wallet_info in enumerate(wallet.addresses):
            print(f"\nWallet {i + 1}:")
            print(f"  Address: {wallet_info['address']}")
            print(f"  Balance: {wallet_info['balance']} LKC")
            print(f"  Transactions: {len(wallet_info['transactions'])}")

            # Show recent transactions
            recent_txs = wallet_info["transactions"][-5:]  # Last 5 transactions
            for tx in recent_txs:
                status = tx.get("status", "unknown")
                confirmations = tx.get("confirmations", 0)
                print(f"    TX: {status} ({confirmations} confirmations)")


if __name__ == "__main__":
    debug_data_files()
    debug_blockchain_transactions()
    debug_wallet_sync()
