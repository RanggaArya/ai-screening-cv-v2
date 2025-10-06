import os
import chromadb
from chromadb.utils import embedding_functions
from pypdf import PdfReader

# --- Konfigurasi ---
GROUND_TRUTH_PATH = "ground_truth_docs"
CHROMA_PATH = "chroma_db_storage"
COLLECTION_NAME = "job_screening_docs"
EMBEDDING_MODEL = "all-MiniLM-L6-v2" # Model embedding yang efisien

# Inisialisasi embedding function
# mengunduh model saat pertama kali dijalankan
sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=EMBEDDING_MODEL
)

# Inisialisasi ChromaDB Client
# menyimpan data di disk pada folder CHROMA_PATH
client = chromadb.PersistentClient(path=CHROMA_PATH)

# Dapatkan atau buat collection baru
collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    embedding_function=sentence_transformer_ef,
    metadata={"hnsw:space": "cosine"} # Menggunakan cosine similarity
)

def ingest_documents():
    """
    Membaca semua file PDF dari folder ground_truth_docs,
    memecahnya menjadi potongan teks, dan memasukkannya ke ChromaDB.
    """
    print("Starting document ingestion...")
    documents = []
    metadatas = []
    ids = []
    doc_id_counter = 1

    for filename in os.listdir(GROUND_TRUTH_PATH):
        if filename.endswith(".pdf"):
            file_path = os.path.join(GROUND_TRUTH_PATH, filename)
            print(f"Processing {filename}...")

            try:
                reader = PdfReader(file_path)
                for page_num, page in enumerate(reader.pages):
                    text = page.extract_text()
                    if text:
                        # Di sini menggunakan satu halaman sebagai satu dokumen
                        # Untuk teks yang sangat panjang, bisa dipecah lebih lanjut
                        documents.append(text)
                        metadatas.append({
                            "source_file": filename,
                            "page": page_num + 1
                        })
                        ids.append(f"doc_{doc_id_counter}")
                        doc_id_counter += 1
            except Exception as e:
                print(f"Error reading {filename}: {e}")

    if documents:
        print(f"Adding {len(documents)} document chunks to the collection...")
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print("Ingestion complete!")
    else:
        print("No documents found to ingest.")

if __name__ == "__main__":
    ingest_documents()