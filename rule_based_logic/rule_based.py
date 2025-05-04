import random
from collections import Counter
from typing import List, Callable, Dict, Any
import statistics

# Deterministic Rule-Based Classifier
class RuleBasedLogClassifier:
    def __init__(self):
        self.rules = {
            "error": "System Error",
            "warn": "Warning",
            "success": "Operation Successful",
            "login": "User Authentication",
            "shutdown": "System Shutdown",
            "start": "System Startup"
        }

    def classify(self, log_entry: str) -> str:
        log_lower = log_entry.lower()
        for keyword, label in self.rules.items():
            if keyword in log_lower:
                return label
        return "Unknown"


# Simulated Generative AI Classifier (non-deterministic)
class GenerativeAISimulator:
    def __init__(self):
        self.known_labels = [
            "System Error", "Warning", "Operation Successful",
            "User Authentication", "System Shutdown", "System Startup", "Unknown"
        ]
        # Simulate model uncertainty by adding plausible but incorrect options
        self.noise_labels = [
            "Data Anomaly", "Performance Degradation", "Unverified Event",
            "Potential Threat", "Ambiguous Log", "Irrelevant Entry"
        ]
        self.all_labels = self.known_labels + self.noise_labels

    def generate_response(self, input_text: str) -> str:
        base_match = None
        input_lower = input_text.lower()
        for keyword in ["error", "warn", "success", "login", "shutdown", "start"]:
            if keyword in input_lower:
                base_match = keyword
                break

        # Base probabilities for first 6 known labels
        if base_match == "error":
            choice_weights = [0.6, 0.2, 0.05, 0.05, 0.05, 0.05]  # 6 items
        elif base_match:
            choice_weights = [0.3, 0.4, 0.1, 0.05, 0.05, 0.1]   # 6 items
        else:
            choice_weights = [0.1, 0.1, 0.1, 0.2, 0.2, 0.3]      # 6 items

        # Add weight for the 7th known label ("Unknown")
        choice_weights.append(0.1)

        # Extend with weights for noise labels (6 items)
        total_weights = choice_weights + [0.1] * len(self.noise_labels)

        # Final check
        assert len(self.all_labels) == len(total_weights), \
            f"Length mismatch: {len(self.all_labels)} labels vs {len(total_weights)} weights"

        weighted_label = random.choices(population=self.all_labels, weights=total_weights, k=1)
        return weighted_label[0]


# Evaluation Utilities
def evaluate_model(model_func: Callable[[str], str], inputs: List[str], runs_per_input: int = 10) -> Dict[str, Any]:
    results = {}
    for idx, entry in enumerate(inputs):
        outputs = [model_func(entry) for _ in range(runs_per_input)]
        unique_outputs = set(outputs)
        most_common = Counter(outputs).most_common(1)[0][0]
        results[f"input_{idx}"] = {
            "input_log": entry,
            "outputs": outputs,
            "unique_outputs_count": len(unique_outputs),
            "most_common_output": most_common,
            "output_variability_score": len(unique_outputs) / runs_per_input
        }
    return results


# Analyze and compare results
def analyze_results(rule_based_results: Dict, ai_simulator_results: Dict):
    rb_variability = [v["output_variability_score"] for v in rule_based_results.values()]
    ai_variability = [v["output_variability_score"] for v in ai_simulator_results.values()]

    print(f"\nRule-Based Classifier - Average Output Variability: {statistics.mean(rb_variability):.2f}")
    print(f"Generative AI Simulator - Average Output Variability: {statistics.mean(ai_variability):.2f}")

    print("\nSample Inconsistent Outputs from Generative AI:")
    for key, val in ai_simulator_results.items():
        if val["unique_outputs_count"] > 1:
            print(f"Input: {val['input_log']}")
            print(f"Outputs: {', '.join(val['outputs'])}")
            print("")


# Example Logs
example_logs = [
    "Error: Failed to connect to database",
    "Warning: Disk space below 10%",
    "User login successful",
    "System shutdown initiated",
    "Received unexpected packet size"
]

if __name__ == "__main__":
    # Initialize models
    rule_based = RuleBasedLogClassifier()
    ai_sim = GenerativeAISimulator()

    # Evaluate both models
    rule_based_results = evaluate_model(rule_based.classify, example_logs, runs_per_input=10)
    ai_simulator_results = evaluate_model(ai_sim.generate_response, example_logs, runs_per_input=10)

    # Analyze and print comparison
    analyze_results(rule_based_results, ai_simulator_results)