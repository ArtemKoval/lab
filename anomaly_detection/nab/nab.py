import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from urllib.request import urlretrieve
import zipfile


# 1. Download and extract the NAB dataset
def download_nab_data():
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

    print(f"NAB dataset extracted to {data_dir}")

    return os.path.join(data_dir, "NAB-master")


# Download the data
nab_path = download_nab_data()


# 2. Explore the dataset structure
def explore_nab_structure(nab_path):
    print("\nNAB directory structure:")
    for root, dirs, files in os.walk(nab_path):
        level = root.replace(nab_path, '').count(os.sep)
        indent = ' ' * 4 * (level)
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 4 * (level + 1)
        for f in files[:5]:  # Show first 5 files in each directory
            print(f"{subindent}{f}")
        if len(files) > 5:
            print(f"{subindent}... and {len(files) - 5} more files")


explore_nab_structure(nab_path)


# 3. Load a sample dataset
def load_nab_data(nab_path, dataset_name="realAWSCloudwatch", file_name="ec2_network_in_5abac7.csv"):
    data_path = os.path.join(nab_path, "data", dataset_name, file_name)
    df = pd.read_csv(data_path)

    # Convert timestamp to datetime and set as index
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)

    return df


# Load NYC Taxi data as an example
nyc_taxi = load_nab_data(nab_path)
print("\nSample data:")
print(nyc_taxi.head())


# 4. Visualize the data with anomalies
def plot_with_anomalies(data, title="", ylabel="Value"):
    plt.figure(figsize=(12, 6))
    plt.plot(data.index, data['value'], label='Value', color='blue')

    if 'anomaly' in data.columns:
        anomalies = data[data['anomaly'] == 1]
        plt.scatter(anomalies.index, anomalies['value'],
                    color='red', label='Anomaly', zorder=5)

    plt.title(title)
    plt.xlabel('Timestamp')
    plt.ylabel(ylabel)
    plt.legend()
    plt.grid(True)
    plt.show()


plot_with_anomalies(nyc_taxi, title="NYC Taxi Passenger Count with Anomalies", ylabel="Passenger Count")


# 5. Basic anomaly detection (using simple threshold as example)
def simple_threshold_detection(data, window_size=24, threshold=3):
    """Simple anomaly detection using rolling mean and standard deviation"""
    rolling_mean = data['value'].rolling(window=window_size).mean()
    rolling_std = data['value'].rolling(window=window_size).std()

    # Identify points outside of mean ± threshold*std
    upper_bound = rolling_mean + threshold * rolling_std
    lower_bound = rolling_mean - threshold * rolling_std

    data['predicted_anomaly'] = ((data['value'] > upper_bound) |
                                 (data['value'] < lower_bound)).astype(int)
    return data


# Apply simple detection
nyc_taxi = simple_threshold_detection(nyc_taxi)

# Plot with detected anomalies
plot_with_anomalies(nyc_taxi, title="NYC Taxi with Detected Anomalies (Simple Threshold)")


# 6. Evaluation metrics (if ground truth anomalies exist)
def evaluate_detection(data):
    if 'anomaly' not in data.columns:
        print("No ground truth anomalies to evaluate against")
        return

    true_positives = ((data['anomaly'] == 1) & (data['predicted_anomaly'] == 1)).sum()
    false_positives = ((data['anomaly'] == 0) & (data['predicted_anomaly'] == 1)).sum()
    false_negatives = ((data['anomaly'] == 1) & (data['predicted_anomaly'] == 0)).sum()

    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    print("\nDetection Performance:")
    print(f"True Positives: {true_positives}")
    print(f"False Positives: {false_positives}")
    print(f"False Negatives: {false_negatives}")
    print(f"Precision: {precision:.2f}")
    print(f"Recall: {recall:.2f}")
    print(f"F1 Score: {f1_score:.2f}")


evaluate_detection(nyc_taxi)


# 7. Function to load all datasets in a category
def load_all_datasets(nab_path, category="realTraffic"):
    data_dir = os.path.join(nab_path, "data", category)
    datasets = {}

    for file in os.listdir(data_dir):
        if file.endswith('.csv'):
            df = pd.read_csv(os.path.join(data_dir, file))
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            datasets[file] = df

    return datasets


# Example: Load all realTraffic datasets
traffic_datasets = load_all_datasets(nab_path)
print(f"\nLoaded {len(traffic_datasets)} datasets from realTraffic category")