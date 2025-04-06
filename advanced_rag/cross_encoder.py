from utils import word_wrap, load_chroma
from pypdf import PdfReader
import os
from dotenv import load_dotenv
import numpy as np
from langchain_community.document_loaders import PyPDFLoader
import chromadb
from chromadb.utils.embedding_functions.sentence_transformer_embedding_function import \
    SentenceTransformerEmbeddingFunction
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    SentenceTransformersTokenTextSplitter,
)
from sentence_transformers import CrossEncoder
import ollama  # Import Ollama instead of OpenAI

# Load environment variables from .env file
load_dotenv()

embedding_function = SentenceTransformerEmbeddingFunction()

# No need for OpenAI API key anymore
# Initialize Ollama client
ollama_client = ollama.Client()  # Assumes Ollama server is running locally

reader = PdfReader("data/Amazon-com-Inc-2024-Proxy-Statement.pdf")
pdf_texts = [p.extract_text().strip() for p in reader.pages]

# Filter the empty strings
pdf_texts = [text for text in pdf_texts if text]

character_splitter = RecursiveCharacterTextSplitter(
    separators=["\n\n", "\n", ". ", " ", ""], chunk_size=1000, chunk_overlap=0
)
character_split_texts = character_splitter.split_text("\n\n".join(pdf_texts))

token_splitter = SentenceTransformersTokenTextSplitter(
    chunk_overlap=0, tokens_per_chunk=256
)

token_split_texts = []
for text in character_split_texts:
    token_split_texts += token_splitter.split_text(text)

chroma_client = chromadb.Client()
chroma_collection = chroma_client.get_or_create_collection(
    "data-collect", embedding_function=embedding_function
)


# extract the embeddings of the token_split_texts
ids = [str(i) for i in range(len(token_split_texts))]

chroma_collection.add(ids=ids, documents=token_split_texts)

count = chroma_collection.count()

query = "What has been the investment in research and development?"

results = chroma_collection.query(
    query_texts=query, n_results=10, include=["documents", "embeddings"]
)

retrieved_documents = results["documents"][0]

for document in results["documents"][0]:
    print(word_wrap(document))
    print("")

cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

pairs = [[query, doc] for doc in retrieved_documents]
scores = cross_encoder.predict(pairs)

print("Scores:")
for score in scores:
    print(score)

print("New Ordering:")
for o in np.argsort(scores)[::-1]:
    print(o + 1)

original_query = (
    "What were the most important factors that contributed to increases in revenue?"
)

generated_queries = [
    "What were the major drivers of revenue growth?",
    "Were there any new product launches that contributed to the increase in revenue?",
    "Did any changes in pricing or promotions impact the revenue growth?",
    "What were the key market trends that facilitated the increase in revenue?",
    "Did any acquisitions or partnerships contribute to the revenue growth?",
]

# concatenate the original query with the generated queries
queries = [original_query] + generated_queries

results = chroma_collection.query(
    query_texts=queries, n_results=10, include=["documents", "embeddings"]
)
retrieved_documents = results["documents"]

# Deduplicate the retrieved documents
unique_documents = set()
for documents in retrieved_documents:
    for document in documents:
        unique_documents.add(document)

unique_documents = list(unique_documents)

pairs = []
for doc in unique_documents:
    pairs.append([original_query, doc])

scores = cross_encoder.predict(pairs)

print("Scores:")
for score in scores:
    print(score)

print("New Ordering:")
for o in np.argsort(scores)[::-1]:
    print(o)

top_indices = np.argsort(scores)[::-1][:5]
top_documents = [unique_documents[i] for i in top_indices]

# Concatenate the top documents into a single context
context = "\n\n".join(top_documents)


# Generate the final answer using Ollama instead of OpenAI
def generate_multi_query(query, context, model="gemma3:1b"):  # Changed default model to llama2
    prompt = f"""
    You are a knowledgeable financial research assistant. 
    Your users are inquiring about an annual report. 
    Based on the following context:

    {context}

    Answer the query: '{query}'
    """

    response = ollama_client.generate(
        model=model,
        prompt=prompt,
    )
    content = response['response']
    content = content.split("\n")
    return content


res = generate_multi_query(query=original_query, context=context)
print("Final Answer:")
print(res)