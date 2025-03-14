import numpy as np
from sklearn.ensemble import IsolationForest

# Simulate historical data

historical_data = np.random.normal(0, 1, 1000).reshape(-1, 1)

historical_data[500:502] = 10  # Inject anomalies

# Historical anomaly detection using Isolation Forest

model = IsolationForest(contamination=0.01)

anomalies = model.fit_predict(historical_data)

# Identify anomalies

anomaly_indices = np.where(anomalies == -1)[0]

print("Anomalies detected at indices:", anomaly_indices)
