import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import mean_absolute_error

# Load the Air Passengers dataset
url = "https://raw.githubusercontent.com/jbrownlee/Datasets/master/airline-passengers.csv"
data = pd.read_csv(url, parse_dates=['Month'], index_col='Month')

# Plot the data
plt.figure(figsize=(10, 6))
plt.plot(data, label='Air Passengers')
plt.title('Monthly Air Passengers (1949-1960)')
plt.xlabel('Year')
plt.ylabel('Number of Passengers')
plt.legend()
plt.show()

# Split the data
train_size = int(len(data) * 0.8)
train, test = data.iloc[:train_size], data.iloc[train_size:]

# Baseline model: Predict the last known value
last_known_value = train.iloc[-1]['Passengers']
predictions = [last_known_value] * len(test)

# Add predictions to the test DataFrame
test['Baseline'] = predictions

# Calculate MAE
mae = mean_absolute_error(test['Passengers'], test['Baseline'])
print(f"Mean Absolute Error (MAE): {mae:.2f}")

# Visualize the results
plt.figure(figsize=(10, 6))
plt.plot(train, label='Training Data')
plt.plot(test['Passengers'], label='Actual Test Data')
plt.plot(test['Baseline'], label='Baseline Predictions', linestyle='--')
plt.title('Baseline Model: Predict the Last Known Value')
plt.xlabel('Year')
plt.ylabel('Number of Passengers')
plt.legend()
plt.show()
