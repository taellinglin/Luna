import random
from luna_economy_simulator import EconomicSimulator
import time


def quick_economy_test():
    """Run a quick economy simulation with realistic initial distribution"""
    print("🚀 Starting realistic economy test...")

    # Realistic initial distribution - not everyone gets the same amount
    config = {
        "num_miners": 50,  # Fewer miners (more realistic)
        "num_merchants": 500,  # More merchants for healthy economy
        "num_consumers": 10000,  # Majority are consumers
        "num_investors": 100,  # Small investor class
        "num_employers": 200,  # Reasonable employer count
        "num_employees": 4000,  # Employees working for employers
        "initial_balances": {
            # Power law distribution - more realistic wealth inequality
            "miner": random.randint(50000, 200000),  # Miners start with more
            "merchant": random.randint(10000, 50000),  # Merchants need capital
            "consumer": random.randint(1000, 10000),  # Regular users
            "investor": random.randint(100000, 500000),  # Wealthy investors
            "employer": random.randint(50000, 300000),  # Business owners
            "employee": random.randint(5000, 30000),  # Working class
        },
        "mining_reward": 1.0,  # Smaller rewards (deflationary pressure)
        "simulation_duration": 180,  # 3 minutes for more cycles
        "economic_cycle_interval": 2,
        "transaction_fee": 0.001,  # Small fee to prevent spam
        "wealth_distribution": "power_law",  # Realistic wealth distribution
    }

    simulator = EconomicSimulator(config)

    try:
        simulator.setup_economy()
        print("✅ Realistic economy setup complete! Running simulation...")
        simulator.run_simulation()
    except KeyboardInterrupt:
        print("\n⏹️ Simulation interrupted")
    except Exception as e:
        print(f"❌ Simulation error: {e}")


# Add this method to your EconomicSimulator class:
def apply_realistic_wealth_distribution(self):
    """Apply realistic power law wealth distribution"""
    print("📊 Applying realistic wealth distribution...")

    # Power law parameters (80/20 rule approximation)
    for actor_type, actors in self.actors_by_type.items():
        if actor_type in ["investor", "employer"]:
            # Wealthy classes get power law distribution
            for i, actor in enumerate(actors):
                # First 20% get 80% of the wealth for this class
                if i < len(actors) * 0.2:
                    wealth_multiplier = random.uniform(3.0, 10.0)
                else:
                    wealth_multiplier = random.uniform(0.1, 1.0)

                actor.balance *= wealth_multiplier
        else:
            # Regular classes get more equal distribution
            for actor in actors:
                actor.balance *= random.uniform(0.5, 2.0)


# Modify your setup_economy method to include this:
def setup_economy(self):
    """Setup the economy with realistic parameters"""
    print("🏛️ Setting up realistic economy...")

    # Create actors with base balances
    self.create_actors()

    # Apply realistic wealth distribution
    self.apply_realistic_wealth_distribution()

    # Calculate total money supply
    total_supply = sum(actor.balance for actor in self.actors)

    print(f"💰 Total initial money supply: {total_supply:,.2f} LKC")
    print(f"📊 Average wealth: {total_supply / len(self.actors):,.2f} LKC")

    # Show wealth distribution statistics
    self.show_wealth_distribution()


def show_wealth_distribution(self):
    """Display wealth distribution statistics"""
    print("\n🏦 Realistic Wealth Distribution:")
    print("-" * 50)

    for actor_type, actors in self.actors_by_type.items():
        balances = [actor.balance for actor in actors]
        avg_balance = sum(balances) / len(balances)
        max_balance = max(balances)
        min_balance = min(balances)

        print(
            f"  {self.get_actor_emoji(actor_type)} {actor_type.capitalize():<10} "
            f"| Actors: {len(actors):>4} | "
            f"Avg: {avg_balance:>8,.0f} LKC | "
            f"Range: {min_balance:>6,.0f}-{max_balance:>8,.0f} LKC"
        )

    # Calculate Gini coefficient
    all_balances = [actor.balance for actor in self.actors]
    gini = self.calculate_gini(all_balances)
    print(f"\n📈 Initial Gini Coefficient: {gini:.3f}")

    # Show wealth concentration
    sorted_balances = sorted(all_balances)
    top_10_percent = sum(sorted_balances[-len(sorted_balances) // 10 :])
    top_1_percent = sum(sorted_balances[-len(sorted_balances) // 100 :])

    print(f"💰 Top 10% hold: {top_10_percent / sum(all_balances) * 100:.1f}% of wealth")
    print(f"💰 Top 1% hold: {top_1_percent / sum(all_balances) * 100:.1f}% of wealth")


def calculate_gini(self, balances):
    """Calculate Gini coefficient for wealth distribution"""
    sorted_balances = sorted(balances)
    n = len(sorted_balances)
    cumulative_sum = 0
    for i, balance in enumerate(sorted_balances):
        cumulative_sum += (i + 1) * balance

    if sum(sorted_balances) == 0:
        return 0

    gini = (2 * cumulative_sum) / (n * sum(sorted_balances)) - (n + 1) / n
    return gini


# Also modify transaction creation for more realism:
def create_realistic_transaction(self, sender, receiver, tx_type="general_transfer"):
    """Create more realistic transaction amounts"""
    base_amount = 0

    if tx_type == "mining_reward":
        base_amount = self.mining_reward * random.uniform(0.8, 1.2)
    elif tx_type == "retail_purchase":
        # Retail purchases: 0.1% to 5% of consumer balance
        base_amount = receiver.balance * random.uniform(0.001, 0.05)
    elif tx_type == "salary_payment":
        # Salaries: 1% to 10% of employer balance, divided among employees
        base_amount = (
            sender.balance
            * random.uniform(0.01, 0.10)
            / len([a for a in self.actors if a.actor_type == "employee"])
        )
    elif tx_type == "investment":
        # Investments: 5% to 20% of investor balance
        base_amount = sender.balance * random.uniform(0.05, 0.20)
    else:  # general_transfer
        # General transfers: 0.1% to 2% of sender balance
        base_amount = sender.balance * random.uniform(0.001, 0.02)

    # Ensure amount is reasonable and sender can afford it
    amount = max(0.01, min(base_amount, sender.balance * 0.9))

    return amount


# Update your economic cycle to use realistic transactions:
def run_economic_cycle(self):
    """Run one economic cycle with realistic transactions"""
    # Use realistic transaction amounts instead of fixed percentages
    for tx_type in self.transaction_weights.keys():
        if random.random() < self.transaction_weights[tx_type]:
            sender, receiver = self.select_transaction_parties(tx_type)
            if sender and receiver and sender != receiver:
                amount = self.create_realistic_transaction(sender, receiver, tx_type)

                # Only proceed if amount is meaningful
                if amount >= 0.01 and sender.balance >= amount:
                    # Apply small transaction fee (goes to miners)
                    fee = amount * self.transaction_fee
                    actual_amount = amount - fee

                    if self.execute_transaction(
                        sender, receiver, actual_amount, tx_type
                    ):
                        # Distribute fee to random miner
                        if fee > 0:
                            miners = self.actors_by_type.get("miner", [])
                            if miners:
                                random_miner = random.choice(miners)
                                random_miner.balance += fee
                                self.transaction_history.append(
                                    {
                                        "from": "transaction_fee",
                                        "to": random_miner.actor_id,
                                        "amount": fee,
                                        "type": "fee_distribution",
                                        "timestamp": time.time(),
                                    }
                                )


if __name__ == "__main__":
    quick_economy_test()
