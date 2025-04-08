import pandas as pd
import matplotlib.pyplot as plt
import os
from urllib.request import urlretrieve
import zipfile


# Option 1: Direct download and access
def download_and_load_aws_data(dataset_name="realAWSCloudwatch", file_name="ec2_cpu_utilization_5f5533.csv"):
    # Download NAB dataset if not exists
    nab_url = "https://github.com/numenta/NAB/archive/master.zip"
    data_dir = "nab_data"

    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    zip_path = os.path.join(data_dir, "NAB-master.zip")

    if not os.path.exists(zip_path):
        print("Downloading NAB dataset...")
        urlretrieve(nab_url, zip_path)
        print("Download complete!")

    # Extract the zip file
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(data_dir)

    # Load specific AWS Cloudwatch file
    data_path = os.path.join(data_dir, "NAB-master", "data", dataset_name, file_name)
    df = pd.read_csv(data_path)

    # Convert timestamp and set as index
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)

    return df


# Option 2: Using Merlion's data loader (recommended)
def load_with_merlion(subset="realAWSCloudwatch"):
    try:
        from ts_datasets.anomaly import NAB
    except ImportError:
        raise ImportError("Please install Merlion's ts_datasets package: pip install salesforce-merlion")

    # Load dataset (will automatically download if not present)
    dataset = NAB(subset=subset)

    # Get first time series in the dataset
    ts, metadata = dataset[0]

    # Combine values and anomalies into one DataFrame
    df = pd.DataFrame({
        'value': ts.iloc[:, 0],  # First column is the metric value
        'anomaly': metadata['anomaly']  # Anomaly labels
    })

    return df


# Example usage
try:
    # Try Merlion first (cleaner interface)
    print("Loading with Merlion...")
    aws_data = load_with_merlion()
    print("Successfully loaded with Merlion")
except Exception as e:
    print(f"Merlion load failed: {e}")
    print("Falling back to direct file access...")
    aws_data = download_and_load_aws_data()
    print("Loaded with direct file access")

# Basic analysis and visualization
print("\nData sample:")
print(aws_data.head())

print("\nBasic statistics:")
print(aws_data.describe())

# Plot the data
plt.figure(figsize=(12, 6))
plt.plot(aws_data.index, aws_data['value'], label='Value', color='blue')

# Plot anomalies if they exist
if 'anomaly' in aws_data.columns:
    anomalies = aws_data[aws_data['anomaly'] == 1]
    plt.scatter(anomalies.index, anomalies['value'],
                color='red', label='Anomaly', zorder=5)

plt.title("AWS CloudWatch Metric with Anomalies")
plt.xlabel("Timestamp")
plt.ylabel("Metric Value")
plt.legend()
plt.grid(True)
plt.show()

# Time features extraction (useful for modeling)
aws_data['hour'] = aws_data.index.hour
aws_data['day_of_week'] = aws_data.index.dayofweek
aws_data['day_of_month'] = aws_data.index.day
aws_data['month'] = aws_data.index.month

print("\nData with time features:")
print(aws_data.head())

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# Prepare features
X = aws_data[['value', 'hour', 'day_of_week']].values
X = StandardScaler().fit_transform(X)

# Fit Isolation Forest
clf = IsolationForest(n_estimators=100, contamination='auto', random_state=42)
aws_data['predicted_anomaly'] = clf.fit_predict(X)

# Visualize results
plt.figure(figsize=(12, 6))
plt.plot(aws_data.index, aws_data['value'], label='Value', color='blue')
anomalies = aws_data[aws_data['predicted_anomaly'] == -1]
plt.scatter(anomalies.index, anomalies['value'],
           color='orange', label='Predicted Anomaly', zorder=5)
plt.title("AWS CloudWatch with Predicted Anomalies")
plt.legend()
plt.show()