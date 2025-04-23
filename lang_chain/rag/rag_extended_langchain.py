import streamlit as st
import os
import tempfile
from typing import List

from langchain_community.document_loaders import (
    PyPDFLoader, TextLoader, UnstructuredWordDocumentLoader, UnstructuredMarkdownLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import Ollama
from langchain.chains import RetrievalQA

# --- Session state initialization ---
if "history" not in st.session_state:
    st.session_state.history = []

# --- Load and parse multiple documents ---
def load_all_documents(uploaded_files) -> List[str]:
    docs = []
    for file in uploaded_files:
        suffix = os.path.splitext(file.name)[-1].lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(file.read())
            tmp_file_path = tmp_file.name

        if suffix == ".pdf":
            loader = PyPDFLoader(tmp_file_path)
        elif suffix == ".txt":
            loader = TextLoader(tmp_file_path, encoding="utf-8")
        elif suffix == ".docx":
            loader = UnstructuredWordDocumentLoader(tmp_file_path)
        elif suffix == ".md":
            loader = UnstructuredMarkdownLoader(tmp_file_path)
        else:
            st.warning(f"Unsupported file format: {suffix}")
            continue

        docs.extend(loader.load())
    return docs

def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    return splitter.split_documents(documents)

@st.cache_resource
def init_vector_store(_docs):
    embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    db = FAISS.from_documents(_docs, embedding_model)
    return db.as_retriever(search_kwargs={"k": 3})

@st.cache_resource
def build_qa_chain(_retriever, model_name):
    llm = Ollama(model=model_name)
    return RetrievalQA.from_chain_type(llm=llm, retriever=_retriever, return_source_documents=True)

# --- Streamlit UI ---
st.set_page_config(page_title="RAG Assistant", layout="wide")
st.title("RAG Application (LangChain + FAISS + Ollama)")

st.sidebar.subheader("Ollama Model Selection")
llm_choice = st.sidebar.selectbox("Model", ["llama3", "mistral", "gemma"])

st.sidebar.subheader("Document Upload")
uploaded_files = st.sidebar.file_uploader(
    "Upload documents (.pdf, .txt, .docx, .md)", type=["pdf", "txt", "docx", "md"], accept_multiple_files=True
)

if uploaded_files:
    with st.spinner("Processing documents..."):
        docs = load_all_documents(uploaded_files)
        chunks = split_documents(docs)
        retriever = init_vector_store(chunks)
        qa_chain = build_qa_chain(retriever, llm_choice)

    st.success(f"{len(docs)} documents loaded, {len(chunks)} chunks processed.")

    query = st.text_input("Ask a question based on the document content:")

    if query:
        with st.spinner("Generating answer..."):
            result = qa_chain.invoke({"query": query})
            st.session_state.history.append({"question": query, "answer": result["result"]})

        st.subheader("Answer")
        st.write(result["result"])

        st.subheader("Source Chunks")
        for i, doc in enumerate(result["source_documents"]):
            st.markdown(f"Chunk {i+1}")
            st.write(doc.page_content[:500])
else:
    st.info("Upload at least one document to begin.")

# --- History viewer ---
if st.session_state.history:
    st.sidebar.subheader("Query History")
    for i, entry in enumerate(reversed(st.session_state.history[-10:])):
        st.sidebar.markdown(f"**Q:** {entry['question']}\n\n**A:** {entry['answer'][:100]}...")
