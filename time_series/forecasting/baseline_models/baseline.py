import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error

# Load the dataset
url = "https://raw.githubusercontent.com/jbrownlee/Datasets/master/airline-passengers.csv"
df = pd.read_csv(url, header=0, index_col=0, parse_dates=True)
df.index.freq = 'MS'

# Plot the dataset
plt.figure(figsize=(10, 6))
plt.plot(df, label='Actual Data')
plt.title('Monthly Airline Passengers (1949-1960)')
plt.xlabel('Date')
plt.ylabel('Number of Passengers')
plt.legend()
plt.show()

# Split the data into train and test sets
train = df.iloc[:-12]  # Use all but the last 12 months for training
test = df.iloc[-12:]   # Use the last 12 months for testing

# Define baseline models
def predict_mean(train, test):
    mean = train.mean()
    predictions = [mean] * len(test)
    return predictions

def predict_last_year_mean(train, test):
    last_year = train.iloc[-12:]
    last_year_mean = last_year.mean()
    predictions = [last_year_mean] * len(test)
    return predictions

def predict_last_known_value(train, test):
    last_value = train.iloc[-1]
    predictions = [last_value] * len(test)
    return predictions

def predict_last_season(train, test):
    last_season = train.iloc[-12:]
    predictions = last_season.values
    return predictions

# Generate predictions
mean_predictions = predict_mean(train, test)
last_year_mean_predictions = predict_last_year_mean(train, test)
last_known_value_predictions = predict_last_known_value(train, test)
last_season_predictions = predict_last_season(train, test)

# Evaluate the models
results = {
    'Predict the Mean': mean_squared_error(test, mean_predictions),
    'Predict Last Year\'s Mean': mean_squared_error(test, last_year_mean_predictions),
    'Predict the Last Known Value': mean_squared_error(test, last_known_value_predictions),
    'Predict the Last Season': mean_squared_error(test, last_season_predictions)
}

for model, mse in results.items():
    print(f'{model}: MSE = {mse:.2f}')

# Plot the predictions
plt.figure(figsize=(12, 8))
plt.plot(test.index, test, label='Actual', color='black', linewidth=2)
plt.plot(test.index, mean_predictions, label='Predict the Mean', linestyle='--')
plt.plot(test.index, last_year_mean_predictions, label='Predict Last Year\'s Mean', linestyle='-.')
plt.plot(test.index, last_known_value_predictions, label='Predict the Last Known Value', linestyle=':')
plt.plot(test.index, last_season_predictions, label='Predict the Last Season', linestyle='-')
plt.title('Baseline Models: Predictions vs Actual')
plt.xlabel('Date')
plt.ylabel('Number of Passengers')
plt.legend()
plt.show()