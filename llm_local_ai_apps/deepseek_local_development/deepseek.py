from openai import OpenAI

client = OpenAI(
    api_key="ollama",
    base_url="http://localhost:11434/v1/"
)

response = client.chat.completions.create(
    model="deepseek-r1:1.5b",
    messages=[
        {"role": "system", "content": "You are an experienced AWS SRE"},
        {"role": "user", "content": "Write bash script to create EC2 instance"}
    ],
    #stream=False
    stream=True
)

#print(response.choices[0].message.content)
for chunk in response:
    print(chunk.choices[0].delta.content, end="", flush=True)
