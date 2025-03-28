import requests
import time
import statistics
import matplotlib.pyplot as plt
from concurrent.futures import ThreadPoolExecutor


class ChaosExperiment:
    def __init__(self, url):
        self.url = url
        self.baseline_latencies = []
        self.stress_latencies = []

    def run_request(self):
        """Make a request and return latency"""
        start = time.time()
        try:
            response = requests.get(self.url, timeout=5)
            latency = time.time() - start
            return latency if response.status_code == 200 else None
        except:
            return None

    def establish_baseline(self, samples=20):
        """Determine normal performance characteristics"""
        with ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(lambda _: self.run_request(), range(samples)))

        self.baseline_latencies = [r for r in results if r is not None]
        avg = statistics.mean(self.baseline_latencies)
        print(f"Baseline established - Average latency: {avg:.3f}s")
        return avg

    def introduce_stress(self, stress_factor=5, duration=60):
        """Simulate increased load"""
        start_time = time.time()
        workers = stress_factor * 5  # Scale worker threads

        while time.time() - start_time < duration:
            with ThreadPoolExecutor(max_workers=workers) as executor:
                results = list(executor.map(lambda _: self.run_request(), range(workers)))
            self.stress_latencies.extend([r for r in results if r is not None])
            time.sleep(1)

        avg = statistics.mean(self.stress_latencies)
        print(f"Stress test complete - Average latency: {avg:.3f}s")
        return avg

    def analyze_results(self):
        """Compare baseline and stress performance"""
        plt.figure(figsize=(10, 5))
        plt.plot(self.baseline_latencies, label='Baseline')
        plt.plot(self.stress_latencies, label='Under Stress')
        plt.xlabel('Request Number')
        plt.ylabel('Latency (seconds)')
        plt.title('System Performance During Chaos Experiment')
        plt.legend()
        plt.show()


if __name__ == "__main__":
    experiment = ChaosExperiment("https://example.com")
    experiment.establish_baseline()
    experiment.introduce_stress()
    experiment.analyze_results()