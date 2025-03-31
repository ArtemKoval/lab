"""
Model Context Protocol Implementation
"""
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
import json
import datetime
import uuid
import numpy as np
from sklearn.linear_model import LogisticRegression

@dataclass
class ModelContext:
    """Base class for model context information"""
    environment: str = "production"
    request_id: str = None
    timestamp: str = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    additional_metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Initialize default values"""
        if self.request_id is None:
            self.request_id = str(uuid.uuid4())
        if self.timestamp is None:
            self.timestamp = datetime.datetime.now(datetime.UTC).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary"""
        return asdict(self)

    def to_json(self) -> str:
        """Serialize context to JSON"""
        return json.dumps(self.to_dict())

class ModelWithContext:
    """Wrapper for models that implements Model Context Protocol"""

    def __init__(self, model, default_context: Optional[ModelContext] = None):
        """Initialize with a model and optional default context"""
        self.model = model
        self.default_context = default_context or ModelContext()

    def predict(self, X, context: Optional[ModelContext] = None):
        """Make prediction with context"""
        current_context = context or self.default_context

        # Log the context
        self._log_context(current_context)

        # Get prediction from underlying model
        prediction = self.model.predict(X)

        # Convert numpy array to list for JSON serialization
        if isinstance(prediction, np.ndarray):
            prediction = prediction.tolist()

        # Return both prediction and context
        return {
            "prediction": prediction,
            "context": current_context.to_dict(),
            "model_type": type(self.model).__name__
        }

    def _log_context(self, context: ModelContext):
        """Log the context (in a real implementation, this would write to a database or file)"""
        print(f"Model executed with context: {context.to_json()}")

# Example usage
if __name__ == "__main__":
    # Create a simple model
    X = np.array([[1, 2], [3, 4], [5, 6]])
    y = np.array([0, 1, 0])
    model = LogisticRegression().fit(X, y)

    # Wrap with Model Context Protocol
    context_aware_model = ModelWithContext(
        model,
        default_context=ModelContext(
            environment="staging",
            user_id="demo_user"
        )
    )

    # Make prediction with default context
    test_data = np.array([[2, 3]])
    result = context_aware_model.predict(test_data)
    print("\nPrediction result with default context:")
    print(json.dumps(result, indent=2))

    # Make prediction with custom context
    custom_context = ModelContext(
        environment="testing",
        user_id="test_user_123",
        additional_metadata={
            "experiment": "A/B test v2",
            "feature_flags": ["new_algorithm"]
        }
    )
    custom_result = context_aware_model.predict(test_data, context=custom_context)
    print("\nPrediction result with custom context:")
    print(json.dumps(custom_result, indent=2))