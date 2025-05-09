from docling.chunking import HybridChunker
from docling.document_converter import DocumentConverter

print("=== Document Conversion ===")
doc = DocumentConverter().convert(source="https://arxiv.org/pdf/2408.09869").document


print("=== Chunking ===")
chunker = HybridChunker()
chunk_iter = chunker.chunk(dl_doc=doc)

for i, chunk in enumerate(chunk_iter):
    print(f"=== {i} ===")
    print(f"chunk.text:\n{f'{chunk.text[:300]}…'!r}")
    print(f"chunk.meta:\n{chunk.meta}")

    enriched_text = chunker.contextualize(chunk=chunk)
    print(f"chunker.contextualize(chunk):\n{f'{enriched_text[:300]}…'!r}")

    print()
