# Time Series Anomaly Detection using Prophet

This project demonstrates how to use Facebook's Prophet library for time series anomaly detection on a popular IoT dataset. The dataset used is the "Occupancy Detection" dataset from the UCI Machine Learning Repository, which contains time-stamped data about room occupancy based on temperature, humidity, light, and CO2 levels.

## Table of Contents
1. [Requirements](#requirements)
2. [Installation](#installation)
3. [Dataset](#dataset)
4. [Running the Code](#running-the-code)
5. [Results](#results)
6. [Customization](#customization)
7. [License](#license)

---

## Requirements

To run this code, you need the following Python libraries installed:

- `pandas`
- `fbprophet`
- `matplotlib`
- `scikit-learn`

---

## Installation

1. Clone this repository

2. Install the required Python libraries:
   ```bash
   pip install pandas fbprophet matplotlib scikit-learn
   ```

---

## Dataset

The dataset used in this project is the **Occupancy Detection** dataset, which is available on the [UCI Machine Learning Repository](https://archive.ics.uci.edu/ml/datasets/Occupancy+Detection+). The dataset contains the following columns:

- `date`: Timestamp of the observation.
- `Temperature`: Temperature in Celsius.
- `Humidity`: Relative humidity in percentage.
- `Light`: Light intensity in Lux.
- `CO2`: CO2 concentration in parts per million (ppm).
- `Occupancy`: Binary indicator of room occupancy (0 or 1).

The dataset is automatically downloaded in the code from the UCI repository.

---

## Running the Code

1. Save the provided Python code in a file named `prophet_anomaly_detection.py`.

2. Run the script:
   ```bash
   python prophet_anomaly_detection.py
   ```

3. The script will:
   - Download the dataset.
   - Preprocess the data.
   - Train a Prophet model on the temperature data.
   - Detect anomalies in the test set.
   - Plot the results with anomalies highlighted.
   - Print the detected anomalies.

---

## Results

The script will generate a plot showing:
- The actual temperature values (blue dots).
- The predicted temperature values (red line).
- The confidence interval (gray shaded area).
- Detected anomalies (red dots).

Additionally, the detected anomalies will be printed in the console.

Example output:
```
Detected Anomalies:
                   ds      y      yhat  yhat_lower  yhat_upper
100 2015-02-04 12:00:00  23.50  22.10      21.80      22.40
150 2015-02-05 18:00:00  24.80  22.50      22.20      22.80
...
```

---

## Customization

You can customize the code to:
- Use a different target variable (e.g., humidity, light, or CO2) by changing the `y` column in the code.
- Adjust the `interval_width` parameter in the Prophet model to change the sensitivity of anomaly detection.
- Use a different dataset by modifying the data loading and preprocessing steps.
