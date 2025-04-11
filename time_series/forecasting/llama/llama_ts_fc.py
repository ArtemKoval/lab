import pandas as pd
import matplotlib.pyplot as plt
import requests
import textwrap

# Load the AirPassengers dataset
url = "https://raw.githubusercontent.com/jbrownlee/Datasets/master/airline-passengers.csv"
df = pd.read_csv(url, parse_dates=['Month'])
df.columns = ['Date', 'Passengers']

# Plot the dataset
plt.figure(figsize=(10, 5))
plt.plot(df['Date'], df['Passengers'], marker='o')
plt.title('Monthly Airline Passengers (1949 - 1960)')
plt.xlabel('Date')
plt.ylabel('Number of Passengers')
plt.grid(True)
plt.tight_layout()
plt.show()

# Prepare a sample of the data as text for LLaMA
sample_text = "\n".join(
    f"{row['Date'].strftime('%Y-%m')}: {int(row['Passengers'])}" for _, row in df.tail(12).iterrows()
)

# Build the prompt for LLaMA
prompt = f"""
You are an expert time series forecaster.

Here are monthly airline passenger numbers for the past 12 months:
{sample_text}

Please provide Python code using a popular open-source library (e.g., Prophet, ARIMA, or statsmodels) to forecast the next 6 months.
Include explanations and comments in the code.
"""

# Send prompt to Ollama (assuming llama3 model is running)
response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "llama3.2:1b",
        "prompt": prompt,
        "stream": False
    }
)

# Get and print response
llama_response = response.json()['response']
print("\nLLaMA 3.2 Response:\n")
print(textwrap.fill(llama_response, width=100))
