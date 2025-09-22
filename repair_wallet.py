#!/usr/bin/env python3
"""
repair_wallet.py - Repair wallet configuration issues
"""
import json
import os

def repair_wallet():
    # Check if wallet config exists
    if not os.path.exists("wallet_config.json"):
        print("❌ wallet_config.json not found")
        return False
    
    try:
        # Load current config
        with open("wallet_config.json", "r") as f:
            config = json.load(f)
        
        # Ensure all required sections exist
        if "security" not in config:
            config["security"] = {}
        
        if "encrypt_wallet" not in config["security"]:
            config["security"]["encrypt_wallet"] = True
        
        # Save repaired config
        with open("wallet_config.json", "w") as f:
            json.dump(config, f, indent=2)
        
        print("✅ Wallet config repaired")
        return True
        
    except Exception as e:
        print(f"❌ Error repairing wallet: {e}")
        return False

def create_fresh_wallet():
    """Create a fresh wallet configuration"""
    fresh_config = {
        "network": {
            "port": 9333,
            "peers": ["127.0.0.1:9333"],
            "discovery_enabled": True,
            "max_peers": 10
        },
        "mining": {
            "mining_reward_address": "",
            "auto_mine": False,
            "mining_fee": 0.001
        },
        "security": {
            "encrypt_wallet": True,
            "auto_backup": True,
            "backup_interval": 3600
        },
        "rpc": {
            "enabled": True,
            "port": 9334,
            "allow_remote": False
        },
        "node": {
            "host": "127.0.0.1",
            "port": 9335
        }
    }
    
    # Backup old config if exists
    if os.path.exists("wallet_config.json"):
        os.rename("wallet_config.json", "wallet_config.json.backup")
        print("💾 Backed up old wallet config")
    
    # Create fresh config
    with open("wallet_config.json", "w") as f:
        json.dump(fresh_config, f, indent=2)
    
    print("✅ Fresh wallet config created")
    return True

if __name__ == "__main__":
    print("🔧 Wallet Repair Tool")
    
    print("1. Trying to repair existing wallet...")
    if not repair_wallet():
        print("2. Creating fresh wallet config...")
        create_fresh_wallet()
    
    print("✅ Repair completed")