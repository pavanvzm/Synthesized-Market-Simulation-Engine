"""Simulation engine for running multi-round market simulations."""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import pandas as pd


class TransactionEvent:
    """Transaction event model."""
    
    def __init__(
        self,
        transaction_id: str,
        persona_id: str,
        persona_type: str,
        round_num: int,
        action: str,
        utility_score: float,
        confidence: float,
        reason: str,
        metadata: Optional[dict[str, Any]] = None,
    ):
        self.transaction_id = transaction_id
        self.persona_id = persona_id
        self.persona_type = persona_type
        self.round_num = round_num
        self.action = action
        self.utility_score = utility_score
        self.confidence = confidence
        self.reason = reason
        self.metadata = metadata or {}
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "transaction_id": self.transaction_id,
            "persona_id": self.persona_id,
            "persona_type": self.persona_type,
            "round_num": self.round_num,
            "action": self.action,
            "utility_score": self.utility_score,
            "confidence": self.confidence,
            "reason": self.reason,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }


class Simulator:
    """Main simulation engine.
    
    Runs multi-round simulations with personas, shocks, and agent decisions.
    """
    
    def __init__(
        self,
        config: Any,
        personas: list[Any],
        llm_client: Optional[Any] = None,
        memory: Optional[Any] = None,
        orchestrator: Optional[Any] = None,
    ):
        """Initialize simulator.
        
        Args:
            config: Configuration instance
            personas: List of persona instances
            llm_client: LLM client instance
            memory: Memory backend instance
            orchestrator: Orchestrator instance
        """
        self.config = config
        self.personas = personas
        self.llm = llm_client
        self.memory = memory
        self.orchestrator = orchestrator
        self.transactions: list[TransactionEvent] = []
        self.metrics: list[dict[str, Any]] = []
        self.token_usage: list[dict[str, Any]] = []
        self.run_id: str = ""
    
    def _generate_run_id(self) -> str:
        """Generate unique run ID."""
        import uuid
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"run_{timestamp}_{uuid.uuid4().hex[:6]}"
    
    def _compute_utility(
        self,
        persona: Any,
        scenario: dict[str, Any],
    ) -> float:
        """Compute utility score for persona given scenario."""
        base_utility = 0.5
        
        # Adjust based on price sensitivity and scenario price change
        if "price_change" in scenario:
            price_impact = scenario["price_change"] * persona.price_sensitivity * 0.3
            base_utility -= price_impact
        
        # Adjust based on brand loyalty
        base_utility += persona.brand_loyalty * 0.2
        
        # Random variation
        import random
        base_utility += random.uniform(-0.1, 0.1)
        
        return max(0.0, min(1.0, base_utility))
    
    def _process_consumer_round(
        self,
        persona: Any,
        scenario: dict[str, Any],
        round_num: int,
    ) -> TransactionEvent:
        """Process consumer decision for a round."""
        import uuid
        
        # Retrieve memories
        memories = []
        if self.memory:
            memories = self.memory.retrieve(
                persona_id=persona.persona_id,
                top_k=self.config.memory_top_k,
            )
        
        # Get decision from orchestrator or compute directly
        if self.orchestrator:
            decision = self.orchestrator.process_consumer_decision(
                persona=persona,
                scenario=scenario,
                memories=memories,
                run_id=self.run_id,
                round_num=round_num,
            )
        else:
            # Direct computation
            utility = self._compute_utility(persona, scenario)
            if utility > 0.7:
                action = "purchase"
            elif utility > 0.4:
                action = "hold"
            elif utility > 0.2:
                action = "switch"
            else:
                action = "churn"
            
            decision = {
                "action": action,
                "confidence": round(utility, 2),
                "reason": f"Utility {utility:.2f}",
                "utility_score": round(utility, 2),
            }
        
        # Create transaction event
        event = TransactionEvent(
            transaction_id=f"txn_{uuid.uuid4().hex[:8]}",
            persona_id=persona.persona_id,
            persona_type="consumer",
            round_num=round_num,
            action=decision.get("action", "hold"),
            utility_score=decision.get("utility_score", 0.5),
            confidence=decision.get("confidence", 0.5),
            reason=decision.get("reason", ""),
            metadata={"segment": persona.segment},
        )
        
        # Store memory
        if self.memory:
            self.memory.store(
                persona_id=persona.persona_id,
                memory_type="transaction",
                content=f"Round {round_num}: {event.action} (utility={event.utility_score:.2f})",
                run_id=self.run_id,
                round_num=round_num,
                metadata={"action": event.action},
            )
        
        # Track token usage if LLM was used
        if self.llm and hasattr(self.llm, 'last_tokens'):
            self.token_usage.append({
                "run_id": self.run_id,
                "round": round_num,
                "persona_id": persona.persona_id,
                "tokens": self.llm.last_tokens,
                "provider": self.llm.provider,
            })
        
        return event
    
    def _process_competitor_round(
        self,
        persona: Any,
        market_state: dict[str, Any],
        round_num: int,
    ) -> TransactionEvent:
        """Process competitor decision for a round."""
        import uuid
        
        if self.orchestrator:
            decision = self.orchestrator.process_competitor_decision(
                persona=persona,
                market_state=market_state,
                run_id=self.run_id,
                round_num=round_num,
            )
        else:
            # Direct computation
            if persona.pricing_aggressiveness > 0.6:
                action = "discount"
            elif persona.innovation_rate > 0.7:
                action = "feature_acceleration"
            elif persona.market_position == "challenger":
                action = "marketing_pivot"
            else:
                action = "no_action"
            
            decision = {
                "action": action,
                "confidence": round(0.5 + persona.innovation_rate * 0.3, 2),
                "reason": f"Strategy: {persona.market_position}",
                "impact_estimate": round(persona.pricing_aggressiveness * 0.5, 2),
            }
        
        event = TransactionEvent(
            transaction_id=f"txn_{uuid.uuid4().hex[:8]}",
            persona_id=persona.persona_id,
            persona_type="competitor",
            round_num=round_num,
            action=decision.get("action", "no_action"),
            utility_score=0.5,
            confidence=decision.get("confidence", 0.5),
            reason=decision.get("reason", ""),
            metadata={
                "company_size": persona.company_size,
                "market_position": persona.market_position,
            },
        )
        
        return event
    
    def run(
        self,
        scenarios: Optional[list[dict[str, Any]]] = None,
    ) -> dict[str, Any]:
        """Run simulation.
        
        Args:
            scenarios: Optional list of scenario shocks per round
        
        Returns:
            Simulation results dictionary
        """
        self.run_id = self._generate_run_id()
        output_path = Path(self.config.output_dir) / self.run_id
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize memory
        if self.memory:
            self.memory.initialize()
        
        # Default scenarios
        if scenarios is None:
            scenarios = [
                {"type": "baseline", "price_change": 0.0},
            ] * self.config.sim_rounds
        
        # Ensure enough scenarios
        while len(scenarios) < self.config.sim_rounds:
            scenarios.append({"type": "baseline", "price_change": 0.0})
        
        print(f"[SIM] Starting run {self.run_id}")
        print(f"[SIM] Personas: {len(self.personas)}, Rounds: {self.config.sim_rounds}")
        
        # Run rounds
        for round_num in range(1, self.config.sim_rounds + 1):
            scenario = scenarios[round_num - 1] if round_num <= len(scenarios) else {"type": "baseline"}
            print(f"[SIM] Round {round_num}/{self.config.sim_rounds}: {scenario.get('type', 'baseline')}")
            
            round_transactions = []
            
            # Process personas in batches
            for i in range(0, len(self.personas), self.config.batch_size):
                batch = self.personas[i:i + self.config.batch_size]
                
                for persona in batch:
                    if persona.persona_type == "consumer":
                        event = self._process_consumer_round(persona, scenario, round_num)
                    else:
                        market_state = {"round": round_num, "scenarios": scenarios[:round_num]}
                        event = self._process_competitor_round(persona, market_state, round_num)
                    
                    round_transactions.append(event)
                    self.transactions.append(event)
            
            # Compute round metrics
            round_metrics = self._compute_round_metrics(round_transactions, round_num)
            self.metrics.append(round_metrics)
        
        # Write outputs
        self._write_outputs(output_path)
        
        print(f"[SIM] Complete. Outputs in {output_path}")
        
        return {
            "run_id": self.run_id,
            "output_path": str(output_path),
            "transactions": len(self.transactions),
            "rounds": self.config.sim_rounds,
        }
    
    def _compute_round_metrics(
        self,
        transactions: list[TransactionEvent],
        round_num: int,
    ) -> dict[str, Any]:
        """Compute metrics for a round."""
        consumer_txns = [t for t in transactions if t.persona_type == "consumer"]
        competitor_txns = [t for t in transactions if t.persona_type == "competitor"]
        
        # Action counts
        actions = {}
        for t in consumer_txns:
            actions[t.action] = actions.get(t.action, 0) + 1
        
        total = len(consumer_txns) if consumer_txns else 1
        
        return {
            "run_id": self.run_id,
            "round": round_num,
            "total_personas": len(transactions),
            "consumers": len(consumer_txns),
            "competitors": len(competitor_txns),
            "purchase_count": actions.get("purchase", 0),
            "hold_count": actions.get("hold", 0),
            "switch_count": actions.get("switch", 0),
            "churn_count": actions.get("churn", 0),
            "purchase_rate": round(actions.get("purchase", 0) / total, 3),
            "churn_rate": round(actions.get("churn", 0) / total, 3),
            "avg_utility": round(sum(t.utility_score for t in consumer_txns) / total, 3) if consumer_txns else 0,
            "avg_confidence": round(sum(t.confidence for t in consumer_txns) / total, 3) if consumer_txns else 0,
        }
    
    def _write_outputs(self, output_path: Path) -> None:
        """Write simulation outputs."""
        # Transactions JSONL
        txn_path = output_path / "transactions.jsonl"
        with open(txn_path, "w") as f:
            for txn in self.transactions:
                f.write(json.dumps(txn.to_dict()) + "\n")
        
        # Metrics CSV
        metrics_df = pd.DataFrame(self.metrics)
        metrics_path = output_path / "metrics.csv"
        metrics_df.to_csv(metrics_path, index=False)
        
        # Token ledger CSV
        if self.token_usage:
            token_df = pd.DataFrame(self.token_usage)
            token_path = output_path / "token_ledger.csv"
            token_df.to_csv(token_path, index=False)
        else:
            # Create empty token ledger
            token_path = output_path / "token_ledger.csv"
            pd.DataFrame(columns=["run_id", "round", "persona_id", "tokens", "provider"]).to_csv(
                token_path, index=False
            )
        
        # Config snapshot
        config_path = output_path / "config.json"
        with open(config_path, "w") as f:
            json.dump(self.config.to_dict(), f, indent=2)
