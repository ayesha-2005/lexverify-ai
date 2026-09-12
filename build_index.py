import json
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


# ==================================================
# PATHS
# ==================================================

ROOT = Path(__file__).resolve().parent

CHUNKS_FILE = ROOT / "data" / "chunks.json"

INDEX_DIR = ROOT / "data" / "faiss_index"

INDEX_FILE = INDEX_DIR / "legal_cases.faiss"

METADATA_FILE = INDEX_DIR / "metadata.json"


# ==================================================
# EMBEDDING MODEL
# ==================================================

EMBEDDING_MODEL = "all-MiniLM-L6-v2"


# ==================================================
# LOAD CHUNKS
# ==================================================

print("Loading chunks...")

with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
    chunks = json.load(f)

print(f"Loaded {len(chunks)} chunks.")


if len(chunks) == 0:
    raise ValueError("chunks.json is empty.")


# ==================================================
# LOAD LOCAL EMBEDDING MODEL
# ==================================================

print()
print("Loading local embedding model...")
print(f"Model: {EMBEDDING_MODEL}")

model = SentenceTransformer(EMBEDDING_MODEL)

print("Embedding model loaded successfully.")


# ==================================================
# GENERATE EMBEDDINGS
# ==================================================

print()
print("Generating embeddings...")

texts = [chunk["text"] for chunk in chunks]

embeddings = model.encode(
    texts,
    convert_to_numpy=True,
    normalize_embeddings=True,
    show_progress_bar=True
)

embeddings = np.asarray(
    embeddings,
    dtype="float32"
)

print()
print(f"Embedding shape: {embeddings.shape}")


# ==================================================
# CREATE FAISS INDEX
# ==================================================

dimension = embeddings.shape[1]

print(f"Embedding dimension: {dimension}")

# Since embeddings are normalized,
# inner product gives cosine similarity.
index = faiss.IndexFlatIP(dimension)

index.add(embeddings)

print(f"FAISS index contains {index.ntotal} vectors.")


# ==================================================
# CREATE INDEX DIRECTORY
# ==================================================

INDEX_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ==================================================
# SAVE FAISS INDEX
# ==================================================

faiss.write_index(
    index,
    str(INDEX_FILE)
)

print()
print("FAISS index saved to:")
print(INDEX_FILE)


# ==================================================
# SAVE METADATA
# ==================================================

metadata = {
    "embedding_model": EMBEDDING_MODEL,
    "dimension": dimension,
    "total_vectors": len(chunks),
    "chunks": chunks
}

with open(
    METADATA_FILE,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        metadata,
        f,
        ensure_ascii=False,
        indent=2
    )


print()
print("Metadata saved to:")
print(METADATA_FILE)


# ==================================================
# FINAL CHECK
# ==================================================

print()
print("==========================================")
print("FAISS INDEX BUILD COMPLETE")
print("==========================================")

print(f"Total chunks : {len(chunks)}")
print(f"FAISS vectors: {index.ntotal}")
print(f"Dimension    : {dimension}")

print()
print("Index file:")
print(INDEX_FILE)

print()
print("Metadata file:")
print(METADATA_FILE)

print("==========================================")