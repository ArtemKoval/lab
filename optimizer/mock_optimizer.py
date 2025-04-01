import time
from statistics import mean
from typing import Callable


class InferenceOptimizer:
    def __init__(self, model_func: Callable):
        self.model_func = model_func
        self.cache = {}
        self.history = []

    def query(self, input_text: str, use_cache: bool = True) -> str:
        start_time = time.time()

        # Check cache first
        if use_cache and input_text in self.cache:
            result = self.cache[input_text]
            latency = time.time() - start_time
            self.history.append(("cache", latency))
            return f"[CACHED] {result}"

        # Run model if not in cache
        result = self.model_func(input_text)
        latency = time.time() - start_time
        self.history.append(("model", latency))

        # Store in cache
        self.cache[input_text] = result
        return result

    def get_stats(self) -> dict :
        cache_hits = [latency for (source, latency) in self.history if source == "cache"]
        model_runs = [latency for (source, latency) in self.history if source == "model"]

        return {
            "total_queries": len(self.history),
            "cache_hits": len(cache_hits),
            "model_runs": len(model_runs),
            "avg_cache_latency": mean(cache_hits) if cache_hits else 0,
            "avg_model_latency": mean(model_runs) if model_runs else 0,
            "cache_hit_rate": len(cache_hits) / len(self.history) if self.history else 0
        }


# Example usage
def expensive_model(text):
    # Simulate an expensive model call
    time.sleep(0.5)
    return f"Processed: {text.upper()}"


optimizer = InferenceOptimizer(expensive_model)

# Run queries
queries = ["hello world", "how are you?", "hello world", "test query", "how are you?"]
for query in queries:
    print(optimizer.query(query))

# Get statistics
stats = optimizer.get_stats()
print("\nOptimization Statistics:")
for k, v in stats.items():
    print(f"{k.replace('_', ' ').title()}: {v:.4f}")