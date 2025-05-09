import uuid

from docling.chunking import HybridChunker
from docling.document_converter import DocumentConverter
from haystack import Document as HaystackDocument
from haystack import Pipeline, component
from haystack.components.embedders import SentenceTransformersDocumentEmbedder
from haystack.components.preprocessors import DocumentCleaner
from haystack.components.writers import DocumentWriter
from haystack_integrations.document_stores.chroma import ChromaDocumentStore

from core.config import settings
from core.logger import get_agent_logger, log_execution
from document.models import Document


@component
class DoclingProcessor:
    def __init__(self):
        self.tokenizer_model = settings.tokenizer_model
        self.logger = get_agent_logger("DoclingProcessor")

    @component.output_types(documents=list[HaystackDocument])
    def run(self, sources: list[str], document_id: str, filename: str):
        documents = []
        converter = DocumentConverter()

        for source in sources:
            try:
                result = converter.convert(source)
                doc = result.document
                chunker = HybridChunker(tokenizer=self.tokenizer_model)
                chunks_list = list(chunker.chunk(dl_doc=doc))
                self.logger.info(f"Created {len(chunks_list)} chunks from {filename}")

                for i, chunk in enumerate(chunks_list):
                    enriched_text = chunker.contextualize(chunk=chunk)
                    meta = {
                        "document_id": document_id,
                        "filename": filename,
                        "chunk_id": str(uuid.uuid4()),
                        "chunk_index": i,
                    }
                    self.logger.info(
                        f"Processing chunk {chunk.meta.export_json_dict()}"
                    )
                    if hasattr(chunk.meta, "headings") and chunk.meta.headings:
                        meta["headings"] = ",".join(chunk.meta.headings)
                    else:
                        meta["headings"] = ""

                    page_nums = []
                    if hasattr(chunk.meta, "doc_items"):
                        for item in chunk.meta.doc_items:
                            if hasattr(item, "prov") and item.prov:
                                for prov in item.prov:
                                    if hasattr(prov, "page_no"):
                                        page_nums.append(prov.page_no)

                    if page_nums:
                        unique_pages = list(set(page_nums))
                        meta["page_nums"] = ",".join(map(str, unique_pages))
                        meta["first_page"] = min(unique_pages)
                    else:
                        meta["page_nums"] = ""
                        meta["first_page"] = 0

                    if hasattr(chunk.meta, "origin") and hasattr(
                        chunk.meta.origin, "filename"
                    ):
                        meta["original_filename"] = chunk.meta.origin.filename

                    documents.append(
                        HaystackDocument(content=enriched_text[:500], meta=meta)
                    )

                self.logger.info(
                    f"Processed {len(documents)} documents from {filename}"
                )
            except Exception as e:
                self.logger.error(f"Error processing {source}: {e}")
                documents.append(
                    HaystackDocument(
                        content=f"Error processing document: {str(e)}",
                        meta={
                            "source": source,
                            "error": str(e),
                            "document_id": document_id,
                            "filename": filename,
                        },
                    )
                )

        return {"documents": documents}


class DocumentProcessor:
    def __init__(self):
        self.embedding_model = settings.embedding_model
        self.logger = get_agent_logger("DocumentProcessor")

    @log_execution
    def process_document(self, document: Document, file_path: str) -> int:
        document_store = ChromaDocumentStore(
            collection_name=document.collection_name,
            persist_path=settings.chroma_persist_directory,
        )

        pipeline = self._create_pipeline(document_store)
        result = pipeline.run(
            {
                "docling_processor": {
                    "sources": [file_path],
                    "document_id": document.id,
                    "filename": document.metadata.filename,
                }
            }
        )
        self.logger.info(f"Pipeline result: {result}")
        chunks_count = result.get("writer", {}).get("documents_written", [])
        self.logger.info(f"Indexed {chunks_count} chunks for document {document.id}")
        return chunks_count

    def _create_pipeline(self, document_store):
        pipeline = Pipeline()

        pipeline.add_component("docling_processor", DoclingProcessor())
        pipeline.add_component("cleaner", DocumentCleaner())
        pipeline.add_component(
            "embedder", SentenceTransformersDocumentEmbedder(model=self.embedding_model)
        )
        pipeline.add_component("writer", DocumentWriter(document_store=document_store))

        pipeline.connect("docling_processor.documents", "cleaner.documents")
        pipeline.connect("cleaner.documents", "embedder.documents")
        pipeline.connect("embedder.documents", "writer.documents")

        return pipeline
