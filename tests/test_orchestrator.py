"""Tests for the multi-agent orchestrator."""

from sim_engine.orchestrator import DebateResult, Orchestrator


def test_orchestrator_initialization():
    """Test that the orchestrator can be initialized correctly."""
    orchestrator = Orchestrator(
        debate_enabled=True,
        debate_entropy_threshold=0.8,
        max_debate_rounds=3,
        max_messages_per_round=4,
    )
    assert orchestrator.debate_enabled is True
    assert orchestrator.debate_threshold == 0.8
    assert orchestrator.max_debate_rounds == 3
    assert orchestrator.max_messages == 4


def test_should_debate():
    """Test the debate decision logic based on entropy."""
    orchestrator = Orchestrator(debate_enabled=True, debate_entropy_threshold=0.5)

    # Decisions with high consensus (low entropy) -> should not debate
    unanimous_decisions = [
        {"action": "purchase", "confidence": 0.9},
        {"action": "purchase", "confidence": 0.8},
    ]
    assert orchestrator._should_debate(unanimous_decisions) is False

    # Mixed decisions (high entropy) -> should debate
    split_decisions = [
        {"action": "purchase", "confidence": 0.9},
        {"action": "churn", "confidence": 0.8},
    ]
    assert orchestrator._should_debate(split_decisions) is True


def test_run_debate():
    """Test running a debate round."""
    orchestrator = Orchestrator(debate_enabled=True, max_debate_rounds=1)

    result = orchestrator.run_debate(
        topic="Price increase of 10%",
        initial_positions=[{"agent_id": "market_analyst_agent", "action": "purchase"}],
        run_id="test_run",
        round_num=1,
    )

    assert isinstance(result, DebateResult)
    assert result.decision == "hold"
    assert len(result.votes) > 0
    assert len(orchestrator._message_history) > 0
