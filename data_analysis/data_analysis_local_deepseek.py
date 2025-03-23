from openai import OpenAI
import pandas as pd

# Function to analyze data using DeepSeek via Ollama
def analyze_data_with_ollama(data_description, data_sample):
    """
    Analyze structured data using DeepSeek via Ollama.
    """
    prompt = f"""
       Your task is to analyze the following dataset and provide insights:

       Dataset Description:
       {data_description}

       Sample Data:
       {data_sample}

       Please:
       1. Identify any missing values, anomalies, or errors in the data.
       2. Summarize the key patterns or trends in the data.
       3. Provide recommendations for data cleaning, transformation, or further analysis.
       """

    # Initialize the OpenAI client for Ollama
    client = OpenAI(
        api_key="ollama",  # API key is not required for Ollama
        base_url="http://localhost:11434/v1/"  # Ollama's API endpoint
    )

    # Stream the response from DeepSeek
    llm_response = client.chat.completions.create(
        model="deepseek-r1",  # Replace with the correct model name for DeepSeek
        messages=[
            {"role": "system", "content": "You are an experienced data analyst."},
            {"role": "user", "content": prompt}
        ],
        stream=True  # Stream the response for large outputs
    )

    # Print the streaming response
    print("=== Data Analysis Insights ===")
    for chunk in llm_response:
        print(chunk.choices[0].delta.content, end="", flush=True)

    return llm_response


# Function to preprocess and analyze data
def main():
    # Load data from a CSV file
    data_file = "data.csv"  # Replace with your dataset file
    df = pd.read_csv(data_file)

    # Describe the dataset
    data_description = f"""
    - Number of Rows: {len(df)}
    - Number of Columns: {len(df.columns)}
    - Columns: {', '.join(df.columns)}
    - Sample Data: {df.head().to_string()}
    """

    # Analyze the data using DeepSeek
    print("=== Analyzing Data with DeepSeek ===")
    analysis_result = analyze_data_with_ollama(data_description, df.head().to_string())

    # Optionally, save the analysis result to a file
    with open("data_analysis_result.txt", "w") as output_file:
        for chunk in analysis_result:
            output_file.write(chunk.choices[0].delta.content)

    print("\n=== Data Analysis Complete ===")


# Entry point
if __name__ == "__main__":
    main()