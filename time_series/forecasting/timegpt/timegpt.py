import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA
from sklearn.metrics import mean_squared_error
from nixtla import NixtlaClient

# Load the dataset
url = "https://raw.githubusercontent.com/jbrownlee/Datasets/master/airline-passengers.csv"
df = pd.read_csv(url, parse_dates=['Month'], index_col='Month')
df.columns = ['Passengers']

# Plot the data
plt.figure(figsize=(10, 6))
plt.plot(df)
plt.title('Monthly Airline Passengers')
plt.xlabel('Date')
plt.ylabel('Passengers')
plt.show()

# ARIMA Model
train_size = int(len(df) * 0.8)
train, test = df.iloc[:train_size], df.iloc[train_size:]

model = ARIMA(train, order=(5, 1, 0))
model_fit = model.fit()
print(model_fit.summary())

forecast = model_fit.forecast(steps=len(test))

rmse = mean_squared_error(test, forecast)
print(f'ARIMA RMSE: {rmse}')

plt.figure(figsize=(10, 6))
plt.plot(train, label='Train')
plt.plot(test, label='Test')
plt.plot(test.index, forecast, label='ARIMA Forecast')
plt.legend()
plt.title('ARIMA Forecast vs Actual')
plt.show()

# TimeGPT-1 with Nixtla
data = df.reset_index()
data.columns = ['ds', 'y']

# Initialize Nixtla client
nixtla_client = NixtlaClient(api_key='your_api_key_here')

# Generate forecasts
forecast_timegpt = nixtla_client.forecast(data, h=len(test), model='timegpt-1')

# Convert forecast to DataFrame
forecast_timegpt = pd.DataFrame(forecast_timegpt)
forecast_timegpt['ds'] = pd.to_datetime(forecast_timegpt['ds'])
forecast_timegpt.set_index('ds', inplace=True)

# Calculate RMSE
rmse_timegpt = mean_squared_error(test['Passengers'], forecast_timegpt['yhat'], squared=False)
print(f'TimeGPT-1 RMSE: {rmse_timegpt}')

# Plot the results
plt.figure(figsize=(10, 6))
plt.plot(train.index, train['Passengers'], label='Train')
plt.plot(test.index, test['Passengers'], label='Test')
plt.plot(forecast_timegpt.index, forecast_timegpt['yhat'], label='TimeGPT-1 Forecast')
plt.legend()
plt.title('TimeGPT-1 Forecast vs Actual')
plt.show()

# Comparison
print(f'ARIMA RMSE: {rmse}')
print(f'TimeGPT-1 RMSE: {rmse_timegpt}')