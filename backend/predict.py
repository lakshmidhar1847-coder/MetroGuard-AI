"""
MetroGuard AI - Inference & Prediction Engine
Loads the trained predictive maintenance model and metadata to evaluate
real-time air compressor telemetry for impending failure risks.
"""

import os
import json
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Union, Any

class MetroGuardPredictor:
    def __init__(self, model_dir: str = None):
        if model_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            model_dir = os.path.join(base_dir, "models")
            
        self.model_path = os.path.join(model_dir, "metroguard_model.pkl")
        self.metadata_path = os.path.join(model_dir, "model_metadata.json")
        
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model artifact not found at {self.model_path}")
        if not os.path.exists(self.metadata_path):
            raise FileNotFoundError(f"Metadata file not found at {self.metadata_path}")
            
        # Load model and metadata
        self.model = joblib.load(self.model_path)
        with open(self.metadata_path, 'r') as f:
            self.metadata = json.load(f)
            
        self.feature_names = self.metadata.get("feature_names", [])
        self.selected_threshold = self.metadata.get("selected_threshold", 0.10)
        self.warning_threshold = self.selected_threshold
        self.high_risk_threshold = 0.70
        
    def classify_status(self, risk_probability: float) -> str:
        if risk_probability < self.warning_threshold:
            return "NORMAL"
        elif risk_probability < self.high_risk_threshold:
            return "WARNING"
        else:
            return "HIGH RISK"

    def predict(self, feature_input: Union[Dict[str, float], pd.DataFrame, list]) -> Dict[str, Any]:
        """
        Accepts a feature dictionary or single-row DataFrame matching the 65 engineered features.
        Returns risk probability, risk percentage, and operational status.
        """
        if isinstance(feature_input, dict):
            # Verify feature presence and order
            missing = [f for f in self.feature_names if f not in feature_input]
            if missing:
                raise ValueError(f"Missing required feature(s): {missing[:5]} (total missing: {len(missing)})")
            df_in = pd.DataFrame([[feature_input[f] for f in self.feature_names]], columns=self.feature_names)
        elif isinstance(feature_input, pd.DataFrame):
            df_in = feature_input[self.feature_names]
        elif isinstance(feature_input, list):
            if len(feature_input) != len(self.feature_names):
                raise ValueError(f"Expected {len(self.feature_names)} features, got {len(feature_input)}")
            df_in = pd.DataFrame([feature_input], columns=self.feature_names)
        else:
            raise TypeError("feature_input must be a Dict, DataFrame, or List")
            
        # Calculate risk probability
        proba = float(self.model.predict_proba(df_in.values)[0, 1])
        pct = round(proba * 100, 2)
        status = self.classify_status(proba)
        
        return {
            "risk_probability": round(proba, 6),
            "risk_percentage": pct,
            "status": status,
            "threshold_used": self.selected_threshold,
            "prediction_horizon_minutes": self.metadata.get("prediction_horizon_minutes", 30),
            "model_name": self.metadata.get("model_name", "MetroGuard Model")
        }

# Global singleton helper
_predictor_instance = None

def get_predictor() -> MetroGuardPredictor:
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = MetroGuardPredictor()
    return _predictor_instance

def predict_risk(feature_dict: Dict[str, float]) -> Dict[str, Any]:
    predictor = get_predictor()
    return predictor.predict(feature_dict)

if __name__ == "__main__":
    predictor = MetroGuardPredictor()
    print(f"Loaded {predictor.metadata['model_name']} with {len(predictor.feature_names)} features.")
    print(f"Decision Threshold: {predictor.selected_threshold}")
    
    # Test with zero vector
    dummy_input = {f: 0.0 for f in predictor.feature_names}
    res = predictor.predict(dummy_input)
    print("Inference Test Result (Baseline Vector):", res)
