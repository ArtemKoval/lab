import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error

# Load the Air Passengers dataset
url = "https://raw.githubusercontent.com/jbrownlee/Datasets/master/airline-passengers.csv"
data = pd.read_csv(url, parse_dates=['Month'], index_col='Month')

# Visualize the data
plt.figure(figsize=(10, 6))
plt.plot(data, label='Air Passengers')
plt.title('Monthly Airline Passengers (1949-1960)')
plt.xlabel('Date')
plt.ylabel('Number of Passengers')
plt.legend()
plt.show()

# Split the data into training and test sets
train_size = int(len(data) * 0.8)
train, test = data.iloc[:train_size], data.iloc[train_size:]

# Implement the mean prediction model
mean_value = train['Passengers'].mean()
predictions = np.full_like(test, mean_value)

# Evaluate the model
mse = mean_squared_error(test['Passengers'], predictions)
print(f'Mean Squared Error: {mse:.2f}')

# Visualize the predictions
plt.figure(figsize=(10, 6))
plt.plot(train, label='Training Data')
plt.plot(test, label='Actual Test Data')
plt.plot(test.index, predictions, label='Mean Prediction', linestyle='--')
plt.title('Mean Prediction Model')
plt.xlabel('Date')
plt.ylabel('Number of Passengers')
plt.legend()
plt.show()
