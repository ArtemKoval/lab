# Step 1: Install RAGAS (run this in your terminal or notebook)
# pip install ragas

# Step 2: Import necessary libraries and define metrics
from ragas import evaluate
from ragas.metrics import precision, recall, f1_score, relevance, fluency, answerability

# Define the metrics
metrics = [precision, recall, f1_score, relevance, fluency, answerability]

# Step 3: Prepare your data
data = [
    {
        "query": "What is the capital of France?",
        "retrieved_documents": [
            "France is a country in Europe. Its capital is Paris.",
            "Paris is known for its art and culture."
        ],
        "generated_answer": "The capital of France is Paris."
    },
    {
        "query": "Who wrote 'To Kill a Mockingbird'?",
        "retrieved_documents": [
            "'To Kill a Mockingbird' is a novel by Harper Lee.",
            "Harper Lee was an American novelist."
        ],
        "generated_answer": "Harper Lee wrote 'To Kill a Mockingbird'."
    }
]

# Step 4: Evaluate the RAG system
results = evaluate(data, metrics)

# Step 5: Analyze the results
print(results)