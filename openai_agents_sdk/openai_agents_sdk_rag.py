from agents import Agent, Runner, OpenAIChatCompletionsModel, function_tool
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
import os

# Load and split the PDF
pdf_path = "bedrock-ug.pdf"  # Replace with your PDF path
loader = PyPDFLoader(pdf_path)
documents = loader.load()

text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
texts = text_splitter.split_documents(documents)

# Create vector store from PDF content
embeddings = OpenAIEmbeddings()
vectorstore = FAISS.from_documents(texts, embeddings)

# Define a retrieval function as a tool
@function_tool
def retrieve_documents(query: str):
    docs = vectorstore.similarity_search(query, k=3)
    return "\n\n".join([doc.page_content for doc in docs])

# Define the RAG agent
model = OpenAIChatCompletionsModel(model="gpt-4")
rag_agent = Agent(
    name="PDF RAG Agent",
    instructions="Answer the user's question based on information retrieved from the PDF.",
    tools=[retrieve_documents],
    model=model
)

# Run the agent with a query
query = "What are the key takeaways from the document?"
response = Runner.run_sync(rag_agent, query)

# Output the response
print(response.final_output)
