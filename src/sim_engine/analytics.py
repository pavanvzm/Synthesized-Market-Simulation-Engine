"""Analytics module using DuckDB for simulation analysis."""

from pathlib import Path
from typing import Any, Optional

import pandas as pd


class Analytics:
    """Analytics engine for simulation results."""
    
    def __init__(self, run_path: str):
        """Initialize analytics.
        
        Args:
            run_path: Path to simulation run directory
        """
        self.run_path = Path(run_path)
        self.transactions_df: Optional[pd.DataFrame] = None
        self.metrics_df: Optional[pd.DataFrame] = None
    
    def load_data(self) -> bool:
        """Load transaction and metrics data.
        
        Returns:
            True if successful
        """
        txn_path = self.run_path / "transactions.jsonl"
        metrics_path = self.run_path / "metrics.csv"
        
        if not txn_path.exists():
            return False
        
        try:
            # Load transactions
            self.transactions_df = pd.read_json(txn_path, lines=True)
            
            # Load metrics
            if metrics_path.exists():
                self.metrics_df = pd.read_csv(metrics_path)
            
            return True
        
        except Exception:
            return False
    
    def compute_summary(self) -> dict[str, Any]:
        """Compute summary statistics.
        
        Returns:
            Summary dictionary
        """
        if self.transactions_df is None:
            return {}
        
        df = self.transactions_df
        
        # Overall stats
        total = len(df)
        consumers = df[df["persona_type"] == "consumer"]
        competitors = df[df["persona_type"] == "competitor"]
        
        # Action distribution
        action_counts = consumers["action"].value_counts().to_dict() if len(consumers) > 0 else {}
        
        # By round
        by_round = []
        if "round_num" in df.columns:
            for round_num in sorted(df["round_num"].unique()):
                round_df = df[df["round_num"] == round_num]
                round_consumers = round_df[round_df["persona_type"] == "consumer"]
                
                if len(round_consumers) > 0:
                    actions = round_consumers["action"].value_counts().to_dict()
                    by_round.append({
                        "round": int(round_num),
                        "total": len(round_consumers),
                        "purchases": actions.get("purchase", 0),
                        "churns": actions.get("churn", 0),
                        "switches": actions.get("switch", 0),
                        "holds": actions.get("hold", 0),
                    })
        
        return {
            "total_transactions": total,
            "consumer_transactions": len(consumers),
            "competitor_transactions": len(competitors),
            "action_distribution": action_counts,
            "by_round": by_round,
        }
    
    def compute_segment_analysis(self) -> dict[str, Any]:
        """Compute segment-level analysis.
        
        Returns:
            Segment analysis dictionary
        """
        if self.transactions_df is None:
            return {}
        
        df = self.transactions_df
        consumers = df[df["persona_type"] == "consumer"]
        
        if len(consumers) == 0 or "metadata" not in df.columns:
            return {}
        
        # Extract segment from metadata
        segments = []
        for _, row in consumers.iterrows():
            meta = row.get("metadata", {})
            if isinstance(meta, dict):
                segments.append(meta.get("segment", "unknown"))
            else:
                segments.append("unknown")
        
        consumers = consumers.copy()
        consumers["segment"] = segments
        
        # Group by segment
        segment_stats = []
        for segment in consumers["segment"].unique():
            seg_df = consumers[consumers["segment"] == segment]
            actions = seg_df["action"].value_counts().to_dict()
            
            segment_stats.append({
                "segment": segment,
                "count": len(seg_df),
                "purchase_rate": round(actions.get("purchase", 0) / len(seg_df), 3) if len(seg_df) > 0 else 0,
                "churn_rate": round(actions.get("churn", 0) / len(seg_df), 3) if len(seg_df) > 0 else 0,
            })
        
        return {
            "segments": segment_stats,
        }
    
    def compute_revenue_estimate(
        self,
        avg_transaction_value: float = 100.0,
    ) -> dict[str, float]:
        """Estimate revenue impact.
        
        Args:
            avg_transaction_value: Average transaction value
        
        Returns:
            Revenue estimates
        """
        if self.transactions_df is None:
            return {}
        
        df = self.transactions_df
        consumers = df[df["persona_type"] == "consumer"]
        
        purchases = len(consumers[consumers["action"] == "purchase"])
        churns = len(consumers[consumers["action"] == "churn"])
        
        gross_revenue = purchases * avg_transaction_value
        churn_loss = churns * avg_transaction_value * 0.5  # Assume 50% LTV loss
        
        return {
            "gross_revenue_estimate": gross_revenue,
            "churn_loss_estimate": churn_loss,
            "net_revenue_estimate": gross_revenue - churn_loss,
        }
    
    def to_duckdb(self) -> Optional[Any]:
        """Load data into DuckDB for advanced queries.
        
        Returns:
            DuckDB connection or None
        """
        try:
            import duckdb
            
            conn = duckdb.connect(":memory:")
            
            if self.transactions_df is not None:
                conn.register("transactions", self.transactions_df)
            
            if self.metrics_df is not None:
                conn.register("metrics", self.metrics_df)
            
            return conn
        
        except ImportError:
            return None
    
    def get_churn_forecast(self) -> dict[str, Any]:
        """Generate churn forecast.
        
        Returns:
            Churn forecast dictionary
        """
        if self.transactions_df is None or self.metrics_df is None:
            return {}
        
        # Get latest churn rate
        latest_metrics = self.metrics_df.iloc[-1] if len(self.metrics_df) > 0 else {}
        current_churn = latest_metrics.get("churn_rate", 0)
        
        # Simple projection (in production use more sophisticated model)
        projected_churn = current_churn * 1.1  # 10% increase assumption
        
        return {
            "current_churn_rate": current_churn,
            "projected_churn_rate": round(projected_churn, 3),
            "trend": "increasing" if projected_churn > current_churn else "stable",
        }
