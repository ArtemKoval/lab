from openai import OpenAI


def analyze_logs_with_ollama(logs):
    # Combine logs into a single string
    log_text = "\n".join(logs)
    prompt = f"""
       Your task is to analyze the following logs and provide insights:

       {log_text}

       Please:
       1. Identify any anomalies or errors in the logs.
       2. Summarize the key events or patterns in the logs.
       3. Provide recommendations for further investigation or action.
       """

    client = OpenAI(
        api_key="ollama",
        base_url="http://localhost:11434/v1/"
    )

    llm_response = client.chat.completions.create(
        model="gemma3",
        messages=[
            {"role": "system", "content": "You are an experienced AWS SRE"},
            {"role": "user", "content": prompt}
        ],
        # stream=False
        stream=True
    )

    # print(response.choices[0].message.content)
    for chunk in llm_response:
        print(chunk.choices[0].delta.content, end="", flush=True)

    return llm_response


def main():
    # Load log data from a file
    with open("logs.txt", "r") as file:
        logs = file.readlines()

    # Preprocess logs (e.g., remove timestamps, etc.)
    cleaned_logs = [log.strip() for log in logs]

    # Analyze the logs
    analysis_result = analyze_logs_with_ollama(cleaned_logs)
    print(analysis_result)


if __name__ == "__main__":
    main()
