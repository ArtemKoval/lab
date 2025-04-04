import chromadb
import pandas as pd
from pypdf import PdfReader


def project_embeddings(embeddings, umap_transform):
    projected_embeddings = umap_transform.transform(embeddings)
    return projected_embeddings


def word_wrap(text, width=87):
    return "\n".join([text[i: i + width] for i in range(0, len(text), width)])


def extract_text_from_pdf(file_path):
    text = []
    with open(file_path, "rb") as f:
        pdf = PdfReader(f)
        for page_num in range(pdf.get_num_pages()):
            page = pdf.get_page(page_num)
            text.append(page.extract_text())
    return "\n".join(text)


def load_chroma(filename, collection_name, embedding_function):
    text = extract_text_from_pdf(filename)
    paragraphs = text.split("\n\n")
    embeddings = [embedding_function(paragraph) for paragraph in paragraphs]
    data = {"text": paragraphs, "embeddings": embeddings}
    df = pd.DataFrame(data)
    collection = chromadb.Client().create_collection(collection_name)

    for ids, row in df.iterrows():
        collection.add(ids=ids, documents=row["text"], embeddings=row["embeddings"])
    return collection
