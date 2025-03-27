"""
LlamaIndex ServiceContext to Settings Migration Example
Complete migration following:
https://docs.llamaindex.ai/en/stable/module_guides/supporting_modules/service_context_migration/
"""

from llama_index.core import Settings, VectorStoreIndex, SimpleDirectoryReader
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.node_parser import SentenceSplitter

# 1. Document Loading
documents = SimpleDirectoryReader("data").load_data()  # assumes you have a "data" folder

# 2. Configure Settings (replaces ServiceContext)
Settings.llm = Ollama(model="deepseek-r1:1.5b", temperature=0.1)
Settings.embed_model = HuggingFaceEmbedding(
    model_name="BAAI/bge-small-en-v1.5"
)
Settings.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=20)
Settings.chunk_size = 512
# Settings.context_window = 4096  # typical context window for gpt-3.5-turbo

# 3. Create Index (automatically uses Settings)
index = VectorStoreIndex.from_documents(documents)

# 4. Create Query Engine (uses configured Settings)
query_engine = index.as_query_engine()

# 5. Example Query
response = query_engine.query("What is the main topic of the documents?")
print(response)

# 6. Alternative: Temporary Settings Override
# custom_llm = Ollama(model="gemma3:latest", temperature=0.2)

custom_response = query_engine.query("Explain in detail about the topic")
print("\nDetailed response (DeepSeek R1):")
print(custom_response)


# Outside context manager, reverts to original settings
default_response = query_engine.query("Summarize briefly")
print("\nDefault settings response:")
print(default_response)

# # 7. Direct Component Passing (alternative approach)
# from llama_index.core.response_synthesizers import get_response_synthesizer
#
# custom_engine = index.as_query_engine(
#     llm=custom_llm,
#     response_synthesizer=get_response_synthesizer(
#         streaming=True,
#         llm=custom_llm
#     )
# )

# streaming_response = custom_engine.query("Stream the response about the topic")
# for text in streaming_response.response_gen:
#     print(text, end="")