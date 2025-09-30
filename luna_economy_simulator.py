# luna_economy_simulator.py
#!/usr/bin/env python3
"""
Luna Economy Simulator - Simulates a complete economy with various actors and transactions
"""

import time
import random
import threading
from typing import List, Dict, Any
import numpy as np
from enum import Enum

# luna_economy_simulator.py
#!/usr/bin/env python3
"""
Luna Economy Simulator - Simulates a complete economy with various actors and transactions
Enhanced with real-time graphing and analytics
"""

import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict

# Set up matplotlib for better styling
plt.style.use("seaborn-v0_8")
sns.set_palette("husl")

# ROYGBIV Color Scheme 🌈
COLORS = {
    "R": "\033[91m",
    "O": "\033[93m",
    "Y": "\033[93m",
    "G": "\033[92m",
    "B": "\033[94m",
    "I": "\033[95m",
    "V": "\033[95m",
    "X": "\033[0m",
    "BOLD": "\033[1m",
}


def color_text(text, color_code):
    return f"{color_code}{text}{COLORS['X']}"


class EconomicActorType(Enum):
    MINER = "⛏️ Miner"
    MERCHANT = "🏪 Merchant"
    CONSUMER = "👤 Consumer"
    INVESTOR = "💼 Investor"
    EMPLOYER = "🏢 Employer"
    EMPLOYEE = "👨‍💼 Employee"


class EconomicActor:
    """Represents an economic actor with specific behaviors"""

    def __init__(
        self, actor_id: int, actor_type: EconomicActorType, initial_balance: float = 0
    ):
        self.actor_id = actor_id
        self.actor_type = actor_type
        self.balance = initial_balance
        self.wallet_address = f"LKC_{actor_type.name.lower()}_{actor_id}"
        self.transaction_history = []
        self.behavior_profile = self._generate_behavior_profile()
        self.wealth = initial_balance
        self.income = 0
        self.expenses = 0
        self.balance_history = [initial_balance]
        self.transaction_times = []

    def _generate_behavior_profile(self):
        """Generate behavior profile based on actor type"""
        base_profile = {
            "transaction_frequency": random.uniform(0.1, 1.0),
            "transaction_amount_mean": random.uniform(1, 100),
            "transaction_amount_std": random.uniform(5, 50),
            "savings_rate": random.uniform(0.05, 0.3),
            "risk_tolerance": random.uniform(0.1, 0.9),
        }

        # Type-specific adjustments
        if self.actor_type == EconomicActorType.MINER:
            base_profile.update(
                {
                    "transaction_frequency": random.uniform(0.05, 0.2),
                    "transaction_amount_mean": random.uniform(50, 200),
                    "savings_rate": random.uniform(0.2, 0.5),
                }
            )
        elif self.actor_type == EconomicActorType.MERCHANT:
            base_profile.update(
                {
                    "transaction_frequency": random.uniform(0.8, 2.0),
                    "transaction_amount_mean": random.uniform(10, 100),
                    "savings_rate": random.uniform(0.1, 0.3),
                }
            )
        elif self.actor_type == EconomicActorType.CONSUMER:
            base_profile.update(
                {
                    "transaction_frequency": random.uniform(0.3, 1.5),
                    "transaction_amount_mean": random.uniform(1, 50),
                    "savings_rate": random.uniform(0.05, 0.2),
                }
            )
        elif self.actor_type == EconomicActorType.INVESTOR:
            base_profile.update(
                {
                    "transaction_frequency": random.uniform(0.1, 0.5),
                    "transaction_amount_mean": random.uniform(100, 500),
                    "risk_tolerance": random.uniform(0.6, 0.95),
                }
            )
        elif self.actor_type == EconomicActorType.EMPLOYER:
            base_profile.update(
                {
                    "transaction_frequency": random.uniform(0.2, 0.8),
                    "transaction_amount_mean": random.uniform(30, 100),
                    "savings_rate": random.uniform(0.1, 0.4),
                }
            )
        elif self.actor_type == EconomicActorType.EMPLOYEE:
            base_profile.update(
                {
                    "transaction_frequency": random.uniform(0.5, 1.2),
                    "transaction_amount_mean": random.uniform(5, 30),
                    "savings_rate": random.uniform(0.05, 0.15),
                }
            )

        return base_profile

    def should_transact(self) -> bool:
        """Determine if this actor should make a transaction"""
        frequency = self.behavior_profile["transaction_frequency"]
        return random.random() < (frequency * 0.1)

    def generate_transaction(
        self, other_actors: List["EconomicActor"]
    ) -> Dict[str, Any]:
        """Generate a transaction based on behavior profile"""
        if self.balance <= 0:
            return None

        mean = self.behavior_profile["transaction_amount_mean"]
        std = self.behavior_profile["transaction_amount_std"]
        amount = max(0.1, np.random.normal(mean, std))
        amount = min(amount, self.balance * 0.9)
        amount = round(amount, 2)

        recipient = self._choose_recipient(other_actors)
        if not recipient:
            return None

        transaction_type = self._determine_transaction_type(recipient)

        return {
            "from": self.wallet_address,
            "to": recipient.wallet_address,
            "amount": amount,
            "type": transaction_type,
            "timestamp": time.time(),
            "actor_types": f"{self.actor_type.value} → {recipient.actor_type.value}",
        }

    def _choose_recipient(self, other_actors: List["EconomicActor"]) -> "EconomicActor":
        """Choose a transaction recipient based on economic relationships"""
        valid_recipients = [
            actor for actor in other_actors if actor.actor_id != self.actor_id
        ]

        if not valid_recipients:
            return None

        weights = []
        for actor in valid_recipients:
            weight = 1.0

            if (
                self.actor_type == EconomicActorType.CONSUMER
                and actor.actor_type == EconomicActorType.MERCHANT
            ):
                weight *= 3.0
            elif (
                self.actor_type == EconomicActorType.EMPLOYER
                and actor.actor_type == EconomicActorType.EMPLOYEE
            ):
                weight *= 4.0
            elif (
                self.actor_type == EconomicActorType.EMPLOYEE
                and actor.actor_type == EconomicActorType.EMPLOYER
            ):
                weight *= 0.1
            elif self.actor_type == EconomicActorType.MERCHANT and actor.actor_type in [
                EconomicActorType.CONSUMER,
                EconomicActorType.MINER,
            ]:
                weight *= 2.0
            elif (
                self.actor_type == EconomicActorType.MINER
                and actor.actor_type == EconomicActorType.CONSUMER
            ):
                weight *= 2.0

            weights.append(weight)

        total_weight = sum(weights)
        if total_weight == 0:
            return random.choice(valid_recipients)

        weights = [w / total_weight for w in weights]
        return random.choices(valid_recipients, weights=weights)[0]

    def _determine_transaction_type(self, recipient: "EconomicActor") -> str:
        """Determine transaction type based on actor roles"""
        type_pairs = {
            (EconomicActorType.CONSUMER, EconomicActorType.MERCHANT): "retail_purchase",
            (EconomicActorType.EMPLOYER, EconomicActorType.EMPLOYEE): "salary_payment",
            (EconomicActorType.MERCHANT, EconomicActorType.MINER): "supply_purchase",
            (EconomicActorType.INVESTOR, EconomicActorType.MERCHANT): "investment",
            (EconomicActorType.MINER, EconomicActorType.CONSUMER): "personal_spending",
            (EconomicActorType.EMPLOYEE, EconomicActorType.MERCHANT): "retail_purchase",
            (EconomicActorType.MERCHANT, EconomicActorType.CONSUMER): "sale",
        }

        return type_pairs.get(
            (self.actor_type, recipient.actor_type), "general_transfer"
        )

    def apply_transaction(self, transaction: Dict[str, Any], is_sender: bool):
        """Apply transaction effects to this actor"""
        amount = transaction["amount"]

        if is_sender:
            self.balance -= amount
            self.expenses += amount
        else:
            self.balance += amount
            self.income += amount

        self.transaction_history.append(transaction)
        self.wealth = self.balance
        self.balance_history.append(self.balance)
        self.transaction_times.append(transaction["timestamp"])


class EconomicSimulator:
    """Simulates a complete economy with various actors and real-time graphing"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._default_config()
        self.actors = []
        self.transactions = []
        self.miners = []
        self.economy_metrics = {
            "gdp": 0,
            "inflation_rate": 0,
            "wealth_gini": 0,
            "velocity_of_money": 0,
            "total_supply": 0,
        }
        self.metric_history = {
            "time": [],
            "gdp": [],
            "wealth_gini": [],
            "velocity": [],
            "total_supply": [],
            "transaction_count": [],
            "avg_transaction_size": [],
        }
        self.running = False
        self.start_time = time.time()
        self.cycle_count = 0
        self.figures = {}

    def _default_config(self) -> Dict[str, Any]:
        return {
            "num_miners": 5,
            "num_merchants": 10,
            "num_consumers": 50,
            "num_investors": 5,
            "num_employers": 3,
            "num_employees": 20,
            "initial_balances": {
                "miner": 1000,
                "merchant": 500,
                "consumer": 100,
                "investor": 2000,
                "employer": 800,
                "employee": 50,
            },
            "mining_reward": 10.0,
            "tax_rate": 0.05,
            "simulation_duration": 300,
            "economic_cycle_interval": 10,
        }

    def setup_economy(self):
        """Set up the economic actors"""
        print(color_text("🏛️ Setting up economy...", COLORS["BOLD"]))

        actor_id = 1

        # Create all actor types
        for actor_type, count in [
            (EconomicActorType.MINER, self.config["num_miners"]),
            (EconomicActorType.MERCHANT, self.config["num_merchants"]),
            (EconomicActorType.CONSUMER, self.config["num_consumers"]),
            (EconomicActorType.INVESTOR, self.config["num_investors"]),
            (EconomicActorType.EMPLOYER, self.config["num_employers"]),
            (EconomicActorType.EMPLOYEE, self.config["num_employees"]),
        ]:
            for i in range(count):
                actor = EconomicActor(
                    actor_id,
                    actor_type,
                    self.config["initial_balances"][actor_type.name.lower()],
                )
                self.actors.append(actor)
                if actor_type == EconomicActorType.MINER:
                    self.miners.append(actor)
                actor_id += 1

        print(
            color_text(
                f"✅ Economy created with {len(self.actors)} actors", COLORS["G"]
            )
        )
        self._print_economy_stats()

    def _print_economy_stats(self):
        """Print initial economy statistics"""
        total_wealth = sum(actor.wealth for actor in self.actors)
        avg_wealth = total_wealth / len(self.actors) if self.actors else 0

        print(
            color_text(f"💰 Total initial wealth: {total_wealth:,.2f} LKC", COLORS["Y"])
        )
        print(color_text(f"📊 Average wealth: {avg_wealth:,.2f} LKC", COLORS["B"]))

        print(color_text("\n🏦 Wealth distribution by actor type:", COLORS["BOLD"]))
        for actor_type in EconomicActorType:
            type_actors = [a for a in self.actors if a.actor_type == actor_type]
            if type_actors:
                total_type_wealth = sum(a.wealth for a in type_actors)
                avg_type_wealth = total_type_wealth / len(type_actors)
                print(
                    color_text(
                        f"  {actor_type.value}: {len(type_actors)} actors, "
                        f"Avg: {avg_type_wealth:,.2f} LKC, Total: {total_type_wealth:,.2f} LKC",
                        COLORS["G"],
                    )
                )

    def simulate_economic_cycle(self):
        """Simulate one economic cycle"""
        self.cycle_count += 1
        current_time = time.time()
        new_transactions = []

        # Simulate mining
        self._simulate_mining(current_time)

        # Simulate transactions
        for actor in self.actors:
            if actor.should_transact():
                transaction = actor.generate_transaction(self.actors)
                if transaction and self._validate_transaction(transaction):
                    sender = next(
                        (
                            a
                            for a in self.actors
                            if a.wallet_address == transaction["from"]
                        ),
                        None,
                    )
                    recipient = next(
                        (
                            a
                            for a in self.actors
                            if a.wallet_address == transaction["to"]
                        ),
                        None,
                    )

                    if sender and recipient and sender.balance >= transaction["amount"]:
                        sender.apply_transaction(transaction, is_sender=True)
                        recipient.apply_transaction(transaction, is_sender=False)
                        new_transactions.append(transaction)

        self.transactions.extend(new_transactions)
        self._update_economic_metrics(current_time)

        return new_transactions

    def _simulate_mining(self, current_time: float):
        """Simulate mining rewards"""
        mining_reward = self.config["mining_reward"]

        for miner in self.miners:
            if random.random() < 0.3:
                reward_amount = mining_reward * random.uniform(0.5, 1.5)
                mining_transaction = {
                    "from": "network_mining_reward",
                    "to": miner.wallet_address,
                    "amount": round(reward_amount, 2),
                    "type": "mining_reward",
                    "timestamp": current_time,
                    "actor_types": "Network → Miner",
                }

                miner.balance += mining_transaction["amount"]
                miner.income += mining_transaction["amount"]
                miner.transaction_history.append(mining_transaction)
                self.transactions.append(mining_transaction)

    def _validate_transaction(self, transaction: Dict[str, Any]) -> bool:
        """Validate transaction parameters"""
        if transaction["amount"] <= 0:
            return False
        sender = next(
            (a for a in self.actors if a.wallet_address == transaction["from"]), None
        )
        if not sender or sender.balance < transaction["amount"]:
            return False
        recipient = next(
            (a for a in self.actors if a.wallet_address == transaction["to"]), None
        )
        if not recipient:
            return False
        return True

    def _update_economic_metrics(self, current_time: float):
        """Update comprehensive economic metrics with history tracking"""
        # Current metrics
        recent_transactions = [
            t
            for t in self.transactions
            if current_time - t["timestamp"] < self.config["economic_cycle_interval"]
        ]
        self.economy_metrics["gdp"] = sum(t["amount"] for t in recent_transactions)

        wealths = [actor.wealth for actor in self.actors]
        if wealths:
            self.economy_metrics["wealth_gini"] = self._calculate_gini(wealths)

        money_supply = sum(actor.balance for actor in self.actors)
        if money_supply > 0:
            self.economy_metrics["velocity_of_money"] = (
                self.economy_metrics["gdp"] / money_supply
            )

        self.economy_metrics["total_supply"] = money_supply

        # Update history
        elapsed = current_time - self.start_time
        self.metric_history["time"].append(elapsed)
        self.metric_history["gdp"].append(self.economy_metrics["gdp"])
        self.metric_history["wealth_gini"].append(self.economy_metrics["wealth_gini"])
        self.metric_history["velocity"].append(
            self.economy_metrics["velocity_of_money"]
        )
        self.metric_history["total_supply"].append(self.economy_metrics["total_supply"])
        self.metric_history["transaction_count"].append(len(self.transactions))

        avg_tx_size = (
            np.mean([t["amount"] for t in recent_transactions])
            if recent_transactions
            else 0
        )
        self.metric_history["avg_transaction_size"].append(avg_tx_size)

    def _calculate_gini(self, wealths: List[float]) -> float:
        """Calculate Gini coefficient for wealth distribution"""
        wealths = sorted(wealths)
        n = len(wealths)
        if n == 0:
            return 0
        total_wealth = sum(wealths)
        if total_wealth == 0:
            return 0
        numerator = sum((i + 1) * wealth for i, wealth in enumerate(wealths))
        denominator = n * sum(wealths)
        return (2 * numerator) / denominator - (n + 1) / n

    def create_comprehensive_charts(self):
        """Create comprehensive charts and visualizations"""
        print(
            color_text(
                "\n📊 Generating comprehensive economic charts...", COLORS["BOLD"]
            )
        )

        # Create figure with subplots
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle(
            "🌙 Luna Economy Simulation - Comprehensive Analysis",
            fontsize=16,
            fontweight="bold",
        )

        # 1. GDP and Economic Activity Over Time
        self._plot_gdp_activity(axes[0, 0])

        # 2. Wealth Distribution and Gini Coefficient
        self._plot_wealth_distribution(axes[0, 1])

        # 3. Transaction Analysis
        self._plot_transaction_analysis(axes[0, 2])

        # 4. Actor Type Performance
        self._plot_actor_performance(axes[1, 0])

        # 5. Money Supply and Velocity
        self._plot_money_metrics(axes[1, 1])

        # 6. Network Activity Heatmap
        self._plot_network_heatmap(axes[1, 2])

        plt.tight_layout()
        plt.savefig("luna_economy_comprehensive.png", dpi=300, bbox_inches="tight")
        print(
            color_text(
                "✅ Charts saved as 'luna_economy_comprehensive.png'", COLORS["G"]
            )
        )

        # Create additional specialized charts
        self._create_specialized_charts()

    def _plot_gdp_activity(self, ax):
        """Plot GDP and economic activity over time"""
        time_data = self.metric_history["time"]

        ax.plot(
            time_data,
            self.metric_history["gdp"],
            "b-",
            alpha=0.7,
            label="GDP per Cycle",
        )
        ax.set_xlabel("Time (seconds)")
        ax.set_ylabel("GDP (LKC)")
        ax.set_title("Economic Activity Over Time")
        ax.grid(True, alpha=0.3)
        ax.legend()

        # Add rolling average
        if len(time_data) > 5:
            window = min(5, len(time_data) // 4)
            gdp_ma = np.convolve(
                self.metric_history["gdp"], np.ones(window) / window, mode="valid"
            )
            ax.plot(
                time_data[window - 1 :],
                gdp_ma,
                "r-",
                linewidth=2,
                label=f"MA ({window} cycles)",
            )
            ax.legend()

    def _plot_wealth_distribution(self, ax):
        """Plot wealth distribution and Gini coefficient"""
        # Wealth distribution histogram
        current_wealths = [actor.wealth for actor in self.actors]
        ax.hist(current_wealths, bins=30, alpha=0.7, color="green", edgecolor="black")
        ax.set_xlabel("Wealth (LKC)")
        ax.set_ylabel("Number of Actors")
        ax.set_title("Final Wealth Distribution")
        ax.grid(True, alpha=0.3)

        # Add Gini coefficient trend in inset
        ax_inset = ax.inset_axes([0.6, 0.6, 0.35, 0.35])
        ax_inset.plot(
            self.metric_history["time"], self.metric_history["wealth_gini"], "r-"
        )
        ax_inset.set_xlabel("Time")
        ax_inset.set_ylabel("Gini")
        ax_inset.set_title("Gini Coefficient")
        ax_inset.grid(True, alpha=0.3)

    def _plot_transaction_analysis(self, ax):
        """Plot transaction type analysis"""
        # Transaction type distribution
        tx_types = defaultdict(float)
        tx_counts = defaultdict(int)

        for tx in self.transactions:
            tx_types[tx["type"]] += tx["amount"]
            tx_counts[tx["type"]] += 1

        if tx_types:
            types = list(tx_types.keys())
            amounts = [tx_types[t] for t in types]
            counts = [tx_counts[t] for t in types]

            x = np.arange(len(types))
            width = 0.35

            bars1 = ax.bar(
                x - width / 2, amounts, width, label="Volume (LKC)", alpha=0.7
            )
            bars2 = ax.bar(x + width / 2, counts, width, label="Count", alpha=0.7)

            ax.set_xlabel("Transaction Type")
            ax.set_ylabel("Amount/Count")
            ax.set_title("Transaction Type Analysis")
            ax.set_xticks(x)
            ax.set_xticklabels(types, rotation=45, ha="right")
            ax.legend()
            ax.grid(True, alpha=0.3)

    def _plot_actor_performance(self, ax):
        """Plot actor type performance metrics"""
        actor_data = []
        for actor_type in EconomicActorType:
            type_actors = [a for a in self.actors if a.actor_type == actor_type]
            if type_actors:
                total_income = sum(a.income for a in type_actors)
                total_expenses = sum(a.expenses for a in type_actors)
                net_income = total_income - total_expenses
                avg_balance = sum(a.balance for a in type_actors) / len(type_actors)

                actor_data.append(
                    {
                        "type": actor_type.value,
                        "net_income": net_income,
                        "avg_balance": avg_balance,
                        "transaction_count": sum(
                            len(a.transaction_history) for a in type_actors
                        ),
                    }
                )

        if actor_data:
            types = [d["type"] for d in actor_data]
            net_incomes = [d["net_income"] for d in actor_data]

            colors = ["green" if ni >= 0 else "red" for ni in net_incomes]
            bars = ax.bar(types, net_incomes, color=colors, alpha=0.7)
            ax.set_xlabel("Actor Type")
            ax.set_ylabel("Net Income (LKC)")
            ax.set_title("Actor Type Performance (Net Income)")
            ax.tick_params(axis="x", rotation=45)
            ax.grid(True, alpha=0.3)

            # Add value labels on bars
            for bar, value in zip(bars, net_incomes):
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height(),
                    f"{value:+.0f}",
                    ha="center",
                    va="bottom",
                )

    def _plot_money_metrics(self, ax):
        """Plot money supply and velocity metrics"""
        time_data = self.metric_history["time"]

        # Primary axis for money supply
        ax1 = ax
        ax1.plot(
            time_data, self.metric_history["total_supply"], "g-", label="Money Supply"
        )
        ax1.set_xlabel("Time (seconds)")
        ax1.set_ylabel("Money Supply (LKC)", color="g")
        ax1.tick_params(axis="y", labelcolor="g")

        # Secondary axis for velocity
        ax2 = ax1.twinx()
        ax2.plot(
            time_data, self.metric_history["velocity"], "b-", label="Velocity of Money"
        )
        ax2.set_ylabel("Velocity of Money", color="b")
        ax2.tick_params(axis="y", labelcolor="b")

        ax1.set_title("Money Supply and Velocity")
        ax1.grid(True, alpha=0.3)

    def _plot_network_heatmap(self, ax):
        """Plot transaction network heatmap"""
        # Create actor type transaction matrix
        actor_types = [atype.value for atype in EconomicActorType]
        n_types = len(actor_types)
        transaction_matrix = np.zeros((n_types, n_types))

        # Count transactions between actor types
        for tx in self.transactions:
            if "→" in tx.get("actor_types", ""):
                parts = tx["actor_types"].split(" → ")
                if len(parts) == 2:
                    from_type, to_type = parts
                    try:
                        from_idx = actor_types.index(from_type)
                        to_idx = actor_types.index(to_type)
                        transaction_matrix[from_idx, to_idx] += tx["amount"]
                    except ValueError:
                        pass

        if np.sum(transaction_matrix) > 0:
            # Normalize for better visualization
            transaction_matrix = np.log1p(transaction_matrix)
            im = ax.imshow(transaction_matrix, cmap="YlOrRd", aspect="auto")

            ax.set_xticks(np.arange(n_types))
            ax.set_yticks(np.arange(n_types))
            ax.set_xticklabels(actor_types, rotation=45, ha="right")
            ax.set_yticklabels(actor_types)
            ax.set_title("Transaction Network Heatmap")

            # Add colorbar
            plt.colorbar(im, ax=ax, label="Log Transaction Volume")

    def _create_specialized_charts(self):
        """Create additional specialized charts"""
        # 1. Wealth evolution for sample actors
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

        # Sample a few actors from each type and plot their wealth evolution
        for actor_type in EconomicActorType:
            type_actors = [a for a in self.actors if a.actor_type == actor_type]
            if type_actors:
                # Sample 2 actors from this type
                sample_actors = random.sample(type_actors, min(2, len(type_actors)))
                for actor in sample_actors:
                    if len(actor.balance_history) > 1:
                        ax1.plot(
                            range(len(actor.balance_history)),
                            actor.balance_history,
                            label=f"{actor_type.value} {actor.actor_id}",
                            alpha=0.7,
                        )

        ax1.set_xlabel("Transaction Sequence")
        ax1.set_ylabel("Balance (LKC)")
        ax1.set_title("Individual Actor Wealth Evolution")
        ax1.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
        ax1.grid(True, alpha=0.3)

        # 2. Transaction size distribution
        tx_amounts = [tx["amount"] for tx in self.transactions]
        ax2.hist(tx_amounts, bins=50, alpha=0.7, color="purple", edgecolor="black")
        ax2.set_xlabel("Transaction Amount (LKC)")
        ax2.set_ylabel("Frequency")
        ax2.set_title("Transaction Size Distribution")
        ax2.set_yscale("log")
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig("luna_economy_specialized.png", dpi=300, bbox_inches="tight")

        # 3. Economic inequality comparison
        fig, ax = plt.subplots(figsize=(10, 6))

        # Lorenz curve
        wealths = sorted([actor.wealth for actor in self.actors])
        total_wealth = sum(wealths)
        cumulative_wealth = np.cumsum(wealths) / total_wealth
        cumulative_population = np.arange(1, len(wealths) + 1) / len(wealths)

        ax.plot(cumulative_population, cumulative_wealth, "b-", label="Lorenz Curve")
        ax.plot([0, 1], [0, 1], "r--", label="Perfect Equality")
        ax.fill_between(cumulative_population, cumulative_wealth, alpha=0.3)

        ax.set_xlabel("Cumulative Population Proportion")
        ax.set_ylabel("Cumulative Wealth Proportion")
        ax.set_title("Lorenz Curve - Wealth Inequality")
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig("luna_economy_inequality.png", dpi=300, bbox_inches="tight")

        print(color_text("✅ Additional charts saved:", COLORS["G"]))
        print(color_text("   - luna_economy_specialized.png", COLORS["B"]))
        print(color_text("   - luna_economy_inequality.png", COLORS["B"]))

    def display_economic_dashboard(self):
        """Display real-time economic dashboard"""
        elapsed = time.time() - self.start_time

        print(color_text("\n" + "=" * 100, COLORS["I"]))
        print(color_text("📈 LUNA ECONOMIC DASHBOARD", COLORS["BOLD"]))
        print(color_text("=" * 100, COLORS["I"]))

        print(
            color_text(
                f"⏱️  Elapsed: {elapsed:.0f}s | Cycles: {self.cycle_count} | Actors: {len(self.actors)}",
                COLORS["B"],
            )
        )
        print(
            color_text(
                f"📊 Transactions: {len(self.transactions)} | GDP/Cycle: {self.economy_metrics['gdp']:,.2f} LKC",
                COLORS["G"],
            )
        )

        print(
            color_text(
                f"💰 Money Supply: {self.economy_metrics['total_supply']:,.2f} LKC",
                COLORS["Y"],
            )
        )
        print(
            color_text(
                f"🏦 Wealth Gini: {self.economy_metrics['wealth_gini']:.3f}",
                COLORS["R"]
                if self.economy_metrics["wealth_gini"] > 0.5
                else COLORS["G"],
            )
        )
        print(
            color_text(
                f"💨 Velocity of Money: {self.economy_metrics['velocity_of_money']:.3f}",
                COLORS["B"],
            )
        )

        # Recent transactions
        recent_txs = self.transactions[-5:]
        if recent_txs:
            print(color_text("\n🔄 Recent Transactions:", COLORS["BOLD"]))
            for tx in recent_txs:
                print(
                    color_text(
                        f"  {tx['actor_types']}: {tx['amount']:,.2f} LKC ({tx['type']})",
                        COLORS["I"],
                    )
                )

        # Actor type statistics
        print(color_text("\n👥 Economic Activity by Sector:", COLORS["BOLD"]))
        for actor_type in EconomicActorType:
            type_actors = [a for a in self.actors if a.actor_type == actor_type]
            if type_actors:
                total_income = sum(a.income for a in type_actors)
                total_expenses = sum(a.expenses for a in type_actors)
                avg_balance = sum(a.balance for a in type_actors) / len(type_actors)

                print(
                    color_text(
                        f"  {actor_type.value}: {len(type_actors)} | "
                        f"Avg Bal: {avg_balance:,.2f} | "
                        f"Income: {total_income:,.2f} | "
                        f"Spent: {total_expenses:,.2f}",
                        COLORS["G"] if total_income > total_expenses else COLORS["R"],
                    )
                )

        print(color_text("=" * 100, COLORS["I"]))

    def run_simulation(self, duration: int = None):
        """Run the economic simulation with real-time charting"""
        if duration is None:
            duration = self.config["simulation_duration"]

        self.running = True
        self.start_time = time.time()
        end_time = self.start_time + duration

        print(
            color_text(
                f"🚀 Starting economic simulation for {duration} seconds...",
                COLORS["BOLD"],
            )
        )

        # Start dashboard update thread
        dashboard_thread = threading.Thread(target=self._dashboard_worker, daemon=True)
        dashboard_thread.start()

        try:
            while time.time() < end_time and self.running:
                self.simulate_economic_cycle()
                time.sleep(1)

        except KeyboardInterrupt:
            print(color_text("\n🛑 Simulation interrupted", COLORS["R"]))
        finally:
            self.running = False
            self._generate_final_report()
            self.create_comprehensive_charts()

    def _dashboard_worker(self):
        """Worker thread to update dashboard periodically"""
        while self.running:
            self.display_economic_dashboard()
            time.sleep(15)

    def _generate_final_report(self):
        """Generate comprehensive final economic report"""
        print(color_text("\n" + "=" * 100, COLORS["I"]))
        print(color_text("📊 FINAL ECONOMIC REPORT", COLORS["BOLD"]))
        print(color_text("=" * 100, COLORS["I"]))

        total_duration = time.time() - self.start_time
        total_transaction_volume = sum(tx["amount"] for tx in self.transactions)
        avg_transaction_size = (
            total_transaction_volume / len(self.transactions)
            if self.transactions
            else 0
        )

        print(color_text(f"⏱️  Total Duration: {total_duration:.0f}s", COLORS["B"]))
        print(color_text(f"📈 Economic Cycles: {self.cycle_count}", COLORS["G"]))
        print(
            color_text(f"💸 Total Transactions: {len(self.transactions)}", COLORS["Y"])
        )
        print(
            color_text(
                f"💰 Total Transaction Volume: {total_transaction_volume:,.2f} LKC",
                COLORS["I"],
            )
        )
        print(
            color_text(
                f"📊 Average Transaction Size: {avg_transaction_size:,.2f} LKC",
                COLORS["V"],
            )
        )

        # Wealth distribution analysis
        wealths = [actor.wealth for actor in self.actors]
        if wealths:
            total_wealth = sum(wealths)
            avg_wealth = total_wealth / len(wealths)
            max_wealth = max(wealths)
            min_wealth = min(wealths)

            print(color_text("\n🏦 Wealth Distribution:", COLORS["BOLD"]))
            print(color_text(f"  Total Wealth: {total_wealth:,.2f} LKC", COLORS["Y"]))
            print(color_text(f"  Average Wealth: {avg_wealth:,.2f} LKC", COLORS["B"]))
            print(
                color_text(
                    f"  Wealth Range: {min_wealth:,.2f} - {max_wealth:,.2f} LKC",
                    COLORS["G"],
                )
            )
            print(
                color_text(
                    f"  Gini Coefficient: {self.economy_metrics['wealth_gini']:.3f}",
                    COLORS["R"]
                    if self.economy_metrics["wealth_gini"] > 0.5
                    else COLORS["G"],
                )
            )

        # Actor type performance
        print(color_text("\n🎭 Performance by Actor Type:", COLORS["BOLD"]))
        for actor_type in EconomicActorType:
            type_actors = [a for a in self.actors if a.actor_type == actor_type]
            if type_actors:
                type_income = sum(a.income for a in type_actors)
                type_expenses = sum(a.expenses for a in type_actors)
                net_income = type_income - type_expenses

                print(
                    color_text(
                        f"  {actor_type.value}: Net {net_income:+,.2f} LKC "
                        f"(Income: {type_income:,.2f}, Expenses: {type_expenses:,.2f})",
                        COLORS["G"] if net_income > 0 else COLORS["R"],
                    )
                )

        # Transaction type analysis
        print(color_text("\n🔄 Transaction Types:", COLORS["BOLD"]))
        tx_types = {}
        for tx in self.transactions:
            tx_type = tx["type"]
            tx_types[tx_type] = tx_types.get(tx_type, 0) + 1

        for tx_type, count in sorted(
            tx_types.items(), key=lambda x: x[1], reverse=True
        ):
            volume = sum(
                tx["amount"] for tx in self.transactions if tx["type"] == tx_type
            )
            print(
                color_text(f"  {tx_type}: {count} txs, {volume:,.2f} LKC", COLORS["I"])
            )


def quick_economy_test():
    """Run a quick economy simulation with enhanced visualization"""
    print("🚀 Starting quick economy test with advanced analytics...")

    config = {
        "num_miners": 5,
        "num_merchants": 8,
        "num_consumers": 30,
        "num_investors": 4,
        "num_employers": 2,
        "num_employees": 15,
        "initial_balances": {
            "miner": 1000,
            "merchant": 300,
            "consumer": 50,
            "investor": 1500,
            "employer": 600,
            "employee": 30,
        },
        "mining_reward": 5.0,
        "simulation_duration": 120,  # 2 minutes for quick test
        "economic_cycle_interval": 5,
    }

    simulator = EconomicSimulator(config)

    try:
        simulator.setup_economy()
        print(
            "✅ Economy setup complete! Running simulation with real-time analytics..."
        )
        simulator.run_simulation()
    except KeyboardInterrupt:
        print("\n⏹️ Simulation interrupted")
    except Exception as e:
        print(f"❌ Simulation error: {e}")


if __name__ == "__main__":
    quick_economy_test()
