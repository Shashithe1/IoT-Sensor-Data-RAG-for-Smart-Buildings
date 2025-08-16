import os
import glob
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from sentence_transformers import SentenceTransformer

# ✅ Import from store
from store import get_vector_client, get_collection


def index_corpus():
    """Load all PDFs from data/manuals and data/specs, split, embed, and add to Chroma"""
    client = get_vector_client()
    col = get_collection(client)

    manuals = glob.glob("data/manuals/*.pdf")
    specs = glob.glob("data/specs/*.pdf")
    pdfs = manuals + specs

    if not pdfs:
        print("⚠️ No documents found in data/manuals or data/specs")
        return

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    for path in pdfs:
        loader = PyPDFLoader(path)
        docs = loader.load()
        chunks = splitter.split_documents(docs)

        texts = [c.page_content for c in chunks]
        metas = [{"source": os.path.basename(path)} for c in chunks]
        embeddings = model.encode(texts).tolist()

        ids = [f"{os.path.basename(path)}_{i}" for i in range(len(texts))]

        col.add(
            ids=ids,
            documents=texts,
            metadatas=metas,
            embeddings=embeddings
        )

    print("✅ Documents indexed successfully.")


def search_docs(query: str, k: int = 3):
    """Query Chroma for most relevant docs"""
    client = get_vector_client()
    col = get_collection(client)
    return col.query(query_texts=[query], n_results=k)
