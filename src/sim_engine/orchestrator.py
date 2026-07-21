"""Multi-agent orchestration module."""

import json
from typing import Any, Optional

from pydantic import BaseModel


class AgentMessage(BaseModel):
    """Message between agents."""
    agent_id: str
    role: str  # consumer_agent, competitor_agent, market_analyst_agent, risk_auditor_agent
    content: str
    round_num: int
    metadata: dict[str, Any] = Field(default_factory=dict)


class DebateResult(BaseModel):
    """Result of multi-agent debate."""
    decision: str
    confidence: float
    reasoning: str
    votes: dict[str, str]
    entropy: float


class Orchestrator:
    """Lightweight multi-agent orchestrator.
    
    Coordinates consumer, competitor, analyst, and risk auditor agents.
    Supports optional debate protocol for high-entropy decisions.
    """
    
    def __init__(
        self,
        llm_client: Any = None,
        debate_enabled: bool = False,
        debate_entropy_threshold: float = 0.85,
        max_debate_rounds: int = 2,
        max_messages_per_round: int = 3,
    ):
        """Initialize orchestrator.
        
        Args:
            llm_client: LLM client instance
            debate_enabled: Enable multi-agent debate
            debate_entropy_threshold: Threshold for triggering debate
            max_debate_rounds: Maximum debate rounds
            max_messages_per_round: Max messages per debate round
        """
        self.llm = llm_client
        self.debate_enabled = debate_enabled
        self.debate_threshold = debate_entropy_threshold
        self.max_debate_rounds = max_debate_rounds
        self.max_messages = max_messages_per_round
        self._message_history: list[AgentMessage] = []
    
    def _compute_entropy(self, probabilities: list[float]) -> float:
        """Compute entropy of probability distribution."""
        import math
        entropy = 0.0
        for p in probabilities:
            if p > 0:
                entropy -= p * math.log2(p)
        return entropy
    
    def _should_debate(self, initial_decisions: list[dict[str, Any]]) -> bool:
        """Determine if debate is needed based on decision entropy."""
        if not self.debate_enabled:
            return False
        
        if len(initial_decisions) < 2:
            return False
        
        # Compute action distribution
        actions = [d.get("action", "unknown") for d in initial_decisions]
        action_counts = {}
        for a in actions:
            action_counts[a] = action_counts.get(a, 0) + 1
        
        # Convert to probabilities
        total = len(actions)
        probs = [c / total for c in action_counts.values()]
        
        # Compute entropy
        max_entropy = math.log2(len(action_counts)) if len(action_counts) > 1 else 1.0
        entropy = self._compute_entropy(probs) / max_entropy if max_entropy > 0 else 0
        
        return entropy > self.debate_threshold
    
    def run_debate(
        self,
        topic: str,
        initial_positions: list[dict[str, Any]],
        run_id: str,
        round_num: int,
    ) -> DebateResult:
        """Run multi-agent debate.
        
        Args:
            topic: Debate topic
            initial_positions: Initial agent positions
            run_id: Simulation run ID
            round_num: Current round
        
        Returns:
            DebateResult with final decision
        """
        import math
        
        roles = ["market_analyst_agent", "risk_auditor_agent"]
        votes = {}
        messages = []
        
        for debate_round in range(self.max_debate_rounds):
            for role in roles:
                if len(messages) >= self.max_messages_per_round:
                    break
                
                # Generate debate message
                system_prompt = f"You are {role}. Analyze the situation and provide reasoned input."
                prompt = f"Topic: {topic}\nCurrent positions: {json.dumps(initial_positions)}\nRound {debate_round + 1}"
                
                if self.llm:
                    response = self.llm.generate(prompt, system_prompt)
                    content = response.content
                else:
                    content = json.dumps({
                        "position": "neutral",
                        "reasoning": "Based on available data",
                    }, indent=2)
                
                msg = AgentMessage(
                    agent_id=role,
                    role=role,
                    content=content,
                    round_num=round_num,
                )
                messages.append(msg)
                self._message_history.append(msg)
        
        # Aggregate votes
        for role in roles:
            votes[role] = "agree"  # Simplified voting
        
        # Compute final decision
        final_decision = "hold"
        confidence = 0.75
        reasoning = "Consensus reached after debate"
        
        # Compute final entropy
        vote_values = list(votes.values())
        vote_counts = {}
        for v in vote_values:
            vote_counts[v] = vote_counts.get(v, 0) + 1
        
        probs = [c / len(vote_values) for c in vote_counts.values()]
        entropy = self._compute_entropy(probs) if probs else 0
        
        return DebateResult(
            decision=final_decision,
            confidence=confidence,
            reasoning=reasoning,
            votes=votes,
            entropy=entropy,
        )
    
    def process_consumer_decision(
        self,
        persona: Any,
        scenario: dict[str, Any],
        memories: list[Any],
        run_id: str,
        round_num: int,
    ) -> dict[str, Any]:
        """Process consumer decision.
        
        Args:
            persona: Consumer persona
            scenario: Current scenario
            memories: Retrieved memories
            run_id: Run ID
            round_num: Round number
        
        Returns:
            Decision dictionary
        """
        # Build prompt
        system_prompt = (
            "You are a consumer agent. Decide whether to purchase, hold, switch, or churn. "
            "Output JSON with: action, confidence, reason, utility_score."
        )
        
        prompt = f"""
Persona: {persona.segment}, price_sensitivity={persona.price_sensitivity}, loyalty={persona.brand_loyalty}
Scenario: {json.dumps(scenario)}
Memories: {[m.content if hasattr(m, 'content') else str(m) for m in memories[:3]]}

Decide your action. Output JSON only.
"""
        
        if self.llm:
            response = self.llm.generate(prompt, system_prompt)
            decision = self.llm.parse_json(response)
        else:
            # Mock decision based on persona attributes
            utility = (1 - persona.price_sensitivity) * 0.5 + persona.brand_loyalty * 0.5
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
                "reason": f"Utility score {utility:.2f} based on preferences",
                "utility_score": round(utility, 2),
            }
        
        return decision
    
    def process_competitor_decision(
        self,
        persona: Any,
        market_state: dict[str, Any],
        run_id: str,
        round_num: int,
    ) -> dict[str, Any]:
        """Process competitor decision.
        
        Args:
            persona: Competitor persona
            market_state: Current market state
            run_id: Run ID
            round_num: Round number
        
        Returns:
            Decision dictionary
        """
        system_prompt = (
            "You are a competitor agent. Decide your strategic response: discount, bundle, "
            "feature_acceleration, marketing_pivot, or no_action. Output JSON."
        )
        
        prompt = f"""
Company: {persona.company_size}, position={persona.market_position}
Innovation rate: {persona.innovation_rate}
Pricing aggressiveness: {persona.pricing_aggressiveness}
Market state: {json.dumps(market_state)}

Decide your competitive response. Output JSON only.
"""
        
        if self.llm:
            response = self.llm.generate(prompt, system_prompt)
            decision = self.llm.parse_json(response)
        else:
            # Mock decision
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
                "reason": f"Strategy based on {persona.market_position} position",
                "impact_estimate": round(persona.pricing_aggressiveness * 0.5, 2),
            }
        
        return decision
    
    def clear_history(self) -> None:
        """Clear message history."""
        self._message_history.clear()
