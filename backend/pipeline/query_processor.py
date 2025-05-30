import openai
from haystack import Document, Pipeline, component
from haystack.components.embedders import SentenceTransformersTextEmbedder
from haystack_integrations.components.retrievers.chroma import ChromaEmbeddingRetriever
from haystack_integrations.document_stores.chroma import ChromaDocumentStore

from core.config import settings
from core.logger import get_agent_logger, log_execution


@component
class OpenAIGenerator:
    def __init__(self, api_key: str, model: str):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        self.logger = get_agent_logger("OpenAIGenerator")

    @component.output_types(generated_text=str, documents=list[Document])
    @log_execution
    def run(self, prompt: str, documents: list[Document]):
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that answers questions based on the provided context. if inefficient or irrelevant use your own knowledge. but if you don't know the answer, say 'I don't know based on the provided information.'"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=500,
            )
            return {
                "generated_text": response.choices[0].message.content,
                "documents": documents,
            }
        except Exception as e:
            self.logger.error(f"OpenAI error: {str(e)}")
            return {"generated_text": f"Error: {str(e)}", "documents": documents}


@component
class PromptBuilder:
    def __init__(self):
        self.logger = get_agent_logger("PromptBuilder")
    @component.output_types(prompt=str)
    @log_execution
    def run(self, documents: list[Document], query: str):
        context_blocks = [
            f"[{i + 1}] {doc.content.strip()}"
            for i, doc in enumerate(documents)
            if doc.content.strip()
        ]
        context = "\n\n".join(context_blocks) if context_blocks else "No relevant context available."

        prompt = (
            f"The following are excerpts from documents:\n\n"
            f"{context}\n\n"
            f"Based on the above, answer the following question:\n\n"
            f"{query}\n\n"
            f"Answer:"
        )

        return {"prompt": prompt}



class QueryProcessor:
    def __init__(self):
        self.logger = get_agent_logger("QueryProcessor")

    def _build_pipeline(self, collection: str) -> Pipeline:
        doc_store = ChromaDocumentStore(
            collection_name=collection,
            persist_path=settings.chroma_persist_directory,
        )

        pipeline = Pipeline()
        pipeline.add_component(
            "embedder", SentenceTransformersTextEmbedder(model=settings.embedding_model)
        )
        pipeline.add_component(
            "retriever", ChromaEmbeddingRetriever(document_store=doc_store)
        )
        pipeline.add_component("prompt", PromptBuilder())
        pipeline.add_component(
            "llm",
            OpenAIGenerator(
                api_key=settings.openai_api_key, model=settings.openai_model
            ),
        )

        pipeline.connect("embedder.embedding", "retriever.query_embedding")
        pipeline.connect("retriever.documents", "prompt.documents")
        pipeline.connect("prompt.prompt", "llm.prompt")
        pipeline.connect("retriever.documents", "llm.documents")

        return pipeline

    @log_execution
    def process_query(
        self, query: str, document_ids: list[str] | None = None, top_k: int = 3
    ):
        if not document_ids:
            raise ValueError("No document IDs provided.")

        results = []

        for doc_id in document_ids:
            try:
                pipeline = self._build_pipeline(f"doc_{doc_id}")
                output = pipeline.run(
                    {
                        "embedder": {"text": query},
                        "retriever": {"top_k": top_k},
                        "prompt": {"query": query},
                    }
                )

                llm_output = output.get("llm", {})
                docs = llm_output.get(
                    "documents", output.get("retriever", {}).get("documents", [])
                )

                for d in docs:
                    self.logger.info(d.meta)

                formatted_docs = [
                    {
                        "content": d.content,
                        "document_id": d.meta.get("document_id", "unknown"),
                        "filename": d.meta.get("filename", "unknown"),
                        "chunk_id": d.meta.get("chunk_id", "unknown"),
                        "page_num": d.meta.get("page_nums", None),
                        "headings": d.meta.get("headings", None),
                        "score": getattr(d, "score", 0.0),
                    }
                    for d in docs
                    if hasattr(d, "content")
                ]

                self.logger.info(
                    f"Processed query for document {doc_id} with {len(formatted_docs)} retrieved chunks"
                )

                results.append(
                    {
                        "document_id": doc_id,
                        "answer": llm_output.get("generated_text", "No answer."),
                        "documents": formatted_docs,
                    }
                )

            except Exception as e:
                self.logger.error(f"Error for doc {doc_id}: {str(e)}")
                results.append(
                    {
                        "document_id": doc_id,
                        "answer": f"Error: {str(e)}",
                        "documents": [],
                    }
                )

        return results
