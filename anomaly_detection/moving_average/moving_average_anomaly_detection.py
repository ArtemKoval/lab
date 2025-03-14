import numpy as np

# Simulate real-time data stream

data_stream = np.random.normal(0, 1, 100)  # Normal data

data_stream[50] = 10  # Inject an anomaly

# Real-time anomaly detection using moving average

window_size = 10

threshold = 3

anomalies = []

for i in range(len(data_stream) - window_size):

    window = data_stream[i:i + window_size]

    mean = np.mean(window)

    std = np.std(window)

    if abs(data_stream[i + window_size] - mean) > threshold * std:
        anomalies.append(i + window_size)

print("Anomalies detected at indices:", anomalies)
