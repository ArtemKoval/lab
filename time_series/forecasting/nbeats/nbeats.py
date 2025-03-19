import matplotlib.pyplot as plt
import pandas as pd
from darts import TimeSeries
from darts.dataprocessing.transformers import Scaler
from darts.models import NBEATSModel
from sklearn.metrics import mean_squared_error

# Load the dataset
url = "https://raw.githubusercontent.com/jbrownlee/Datasets/master/airline-passengers.csv"
df = pd.read_csv(url, parse_dates=['Month'], index_col='Month')

# Convert to TimeSeries
series = TimeSeries.from_dataframe(df, value_cols=['Passengers'])

# Split the data into train and test sets
train, test = series.split_before(0.8)

# Scale the data
scaler = Scaler()
train_scaled = scaler.fit_transform(train)
test_scaled = scaler.transform(test)

# Fit N-BEATS model
model = NBEATSModel(input_chunk_length=24, output_chunk_length=12, n_epochs=100)
model.fit(train_scaled)

# Forecast
forecast = model.predict(n=len(test_scaled))
forecast = scaler.inverse_transform(forecast)

# Calculate MSE
mse = mean_squared_error(test.values(), forecast.values())
print(f'MSE: {mse}')

# Plot the results
plt.figure(figsize=(10, 6))
train.plot(label='Train')
test.plot(label='Test')
forecast.plot(label='N-BEATS Forecast')
plt.legend()
plt.show()