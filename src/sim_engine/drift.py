"""Drift monitoring using Evidently AI."""

import json
from pathlib import Path
from typing import Any, Optional

import pandas as pd


class DriftMonitor:
    """Monitor behavioral drift between simulation runs."""
    
    def __init__(self):
        """Initialize drift monitor."""
        self.baseline_df: Optional[pd.DataFrame] = None
        self.current_df: Optional[pd.DataFrame] = None
    
    def load_runs(self, baseline_path: str, current_path: str) -> bool:
        """Load baseline and current run data.
        
        Args:
            baseline_path: Path to baseline run directory
            current_path: Path to current run directory
        
        Returns:
            True if successful
        """
        try:
            # Load baseline transactions
            baseline_txn = Path(baseline_path) / "transactions.jsonl"
            if baseline_txn.exists():
                self.baseline_df = pd.read_json(baseline_txn, lines=True)
            
            # Load current transactions
            current_txn = Path(current_path) / "transactions.jsonl"
            if current_txn.exists():
                self.current_df = pd.read_json(current_txn, lines=True)
            
            return self.baseline_df is not None and self.current_df is not None
        
        except Exception:
            return False
    
    def compute_drift(self) -> dict[str, Any]:
        """Compute drift metrics.
        
        Returns:
            Drift analysis dictionary
        """
        if self.baseline_df is None or self.current_df is None:
            return {}
        
        # Action distribution drift
        baseline_actions = self.baseline_df[self.baseline_df["persona_type"] == "consumer"]["action"].value_counts().to_dict()
        current_actions = self.current_df[self.current_df["persona_type"] == "consumer"]["action"].value_counts().to_dict()
        
        action_drift = {}
        all_actions = set(baseline_actions.keys()) | set(current_actions.keys())
        for action in all_actions:
            baseline_rate = baseline_actions.get(action, 0) / len(self.baseline_df[self.baseline_df["persona_type"] == "consumer"]) if len(self.baseline_df[self.baseline_df["persona_type"] == "consumer"]) > 0 else 0
            current_rate = current_actions.get(action, 0) / len(self.current_df[self.current_df["persona_type"] == "consumer"]) if len(self.current_df[self.current_df["persona_type"] == "consumer"]) > 0 else 0
            drift = current_rate - baseline_rate
            action_drift[action] = {
                "baseline": round(baseline_rate, 3),
                "current": round(current_rate, 3),
                "delta": round(drift, 3),
            }
        
        # Utility score drift
        baseline_utility = self.baseline_df[self.baseline_df["persona_type"] == "consumer"]["utility_score"].mean() if "utility_score" in self.baseline_df.columns else 0
        current_utility = self.current_df[self.current_df["persona_type"] == "consumer"]["utility_score"].mean() if "utility_score" in self.current_df.columns else 0
        
        # Churn risk drift
        baseline_churn = len(self.baseline_df[(self.baseline_df["persona_type"] == "consumer") & (self.baseline_df["action"] == "churn")]) / len(self.baseline_df[self.baseline_df["persona_type"] == "consumer"]) if len(self.baseline_df[self.baseline_df["persona_type"] == "consumer"]) > 0 else 0
        current_churn = len(self.current_df[(self.current_df["persona_type"] == "consumer") & (self.current_df["action"] == "churn")]) / len(self.current_df[self.current_df["persona_type"] == "consumer"]) if len(self.current_df[self.current_df["persona_type"] == "consumer"]) > 0 else 0
        
        return {
            "action_drift": action_drift,
            "utility_drift": {
                "baseline": round(baseline_utility, 3),
                "current": round(current_utility, 3),
                "delta": round(current_utility - baseline_utility, 3),
            },
            "churn_drift": {
                "baseline": round(baseline_churn, 3),
                "current": round(current_churn, 3),
                "delta": round(current_churn - baseline_churn, 3),
            },
            "overall_drift_detected": any(abs(v["delta"]) > 0.1 for v in action_drift.values()),
        }
    
    def generate_evidently_report(self, output_path: str) -> bool:
        """Generate Evidently HTML report.
        
        Args:
            output_path: Path for output HTML file
        
        Returns:
            True if successful
        """
        try:
            from evidently import ColumnMapping
            from evidently.report import Report
            from evidently.metrics import DataDriftTable, DataQualityMetrics
            
            if self.baseline_df is None or self.current_df is None:
                return False
            
            # Prepare reference and current data
            reference = self.baseline_df[self.baseline_df["persona_type"] == "consumer"][["utility_score", "confidence"]].copy()
            current = self.current_df[self.current_df["persona_type"] == "consumer"][["utility_score", "confidence"]].copy()
            
            column_mapping = ColumnMapping(
                target=None,
                prediction="utility_score",
            )
            
            report = Report(metrics=[
                DataDriftTable(),
                DataQualityMetrics(),
            ])
            
            report.run(reference_data=reference, current_data=current, column_mapping=column_mapping)
            
            # Save HTML
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            report.save_html(output_path)
            
            return True
        
        except ImportError:
            # Evidently not installed - save JSON instead
            drift_data = self.compute_drift()
            json_path = output_path.replace(".html", ".json")
            Path(json_path).parent.mkdir(parents=True, exist_ok=True)
            with open(json_path, "w") as f:
                json.dump(drift_data, f, indent=2)
            return True
        
        except Exception:
            return False
