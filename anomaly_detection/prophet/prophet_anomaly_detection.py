import pandas as pd
from prophet import Prophet
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error

# Load the dataset
# url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00357/occupancy_data.zip"
url = "https://raw.githubusercontent.com/pcko1/occupancy-detection/refs/heads/master/Datasets/datatest.txt"
# df = pd.read_csv(url, compression='zip')
df = pd.read_csv(url)

# Select relevant columns and rename them for Prophet
df = df[['date', 'Temperature', 'Humidity', 'Light', 'CO2', 'Occupancy']]
df['date'] = pd.to_datetime(df['date'])
df = df.rename(columns={'date': 'ds', 'Temperature': 'y'})

# Split the data into training and testing sets
train_size = int(len(df) * 0.8)
train, test = df.iloc[:train_size], df.iloc[train_size:]

# Initialize and fit the Prophet model
model = Prophet(interval_width=0.95)  # 95% confidence interval
model.fit(train[['ds', 'y']])

# Make predictions on the test set
forecast = model.predict(test[['ds']])

# Merge the forecast with the actual values
results = test[['ds', 'y']].merge(forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']], on='ds')

# Calculate the error and identify anomalies
results['error'] = results['y'] - results['yhat']
results['anomaly'] = (results['y'] < results['yhat_lower']) | (results['y'] > results['yhat_upper'])

# Plot the results
plt.figure(figsize=(12, 6))
plt.plot(results['ds'], results['y'], 'b.', label='Actual')
plt.plot(results['ds'], results['yhat'], 'r-', label='Predicted')
plt.fill_between(results['ds'], results['yhat_lower'], results['yhat_upper'], color='gray', alpha=0.2, label='Confidence Interval')
plt.scatter(results[results['anomaly']]['ds'], results[results['anomaly']]['y'], color='red', label='Anomaly')
plt.legend()
plt.xlabel('Date')
plt.ylabel('Temperature')
plt.title('Time Series Anomaly Detection using Prophet')
plt.show()

# Print the anomalies
anomalies = results[results['anomaly']]
print("Detected Anomalies:")
print(anomalies[['ds', 'y', 'yhat', 'yhat_lower', 'yhat_upper']])