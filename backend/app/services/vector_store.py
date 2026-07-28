import json
from dataclasses import dataclass
from pathlib import Path
print("******** LOADED vector_store.py ********")
from app.core.config import get_settings
from app.services.embedding import HashingEmbedder, cosine_similarity
from app.services.text_processing import chunk_text, read_text_file


@dataclass
class RetrievedChunk:
    role: str
    source: str
    chunk_id: str
    text: str
    score: float

    def as_dict(self) -> dict:
        return {
            "role": self.role,
            "source": self.source,
            "chunk_id": self.chunk_id,
            "text": self.text,
            "score": round(self.score, 4),
        }


class VectorStore:
    def __init__(self):
        settings = get_settings()
        self.path = settings.vector_store_path
        self.kb_dir = settings.knowledge_base_dir
        print("Knowledge Base Directory:", self.kb_dir)
        print("Vector Store File:", self.path)
        self.embedder = HashingEmbedder(settings.embedding_dimensions)
        self.records: list[dict] = []
        self.load_or_build()
        

    def load_or_build(self) -> None:
        print("load_or_build() called")
        print("Vector Store Path:", self.path.resolve())
        if self.path.exists():
            self.records = json.loads(self.path.read_text(encoding="utf-8"))

            print("Loaded records:", len(self.records))

            return
        
        print("Calling rebuild()")
        
        self.rebuild()

    def rebuild(self) -> None:
        
        self.path.parent.mkdir(parents=True, exist_ok=True)
        
        print("Knowledge Base Exists:", self.kb_dir.exists())
        print("Knowledge Base Path:", self.kb_dir.resolve())
        records: list[dict] = []
        for role_dir in sorted(self.kb_dir.glob("*")):
            if not role_dir.is_dir():
                continue
            role = role_dir.name.replace("_", " ")
            for source_path in sorted(list(role_dir.glob("*.txt")) + list(role_dir.glob("*.pdf"))):
                print(f"\nSTART READING: {source_path.name}")
                print("INDEXING:", source_path.name)
                    
                    
                    
                text = read_source(source_path)
                print(f"FINISHED READING: {source_path.name}")

                chunks = chunk_text(text)
                print(f"FINISHED CHUNKING: {source_path.name}")

                for index, chunk in enumerate(chunks):    
                
                    
                    
                    records.append(
                        {
                            "role": role,
                            "source": source_path.name,
                            "chunk_id": f"{source_path.stem}-{index}",
                            "text": chunk,
                            "embedding": self.embedder.embed(chunk),
                        }
                    )
            print("Total records built:", len(records))
            
        print("Finished chunking.")
        self.records = records
        print("Assigned self.records")
        self.path.write_text(json.dumps(records, indent=2), encoding="utf-8")
        print("vector_store.json written successfully") 

    def roles(self) -> list[str]:
        return sorted({record["role"] for record in self.records})

    def search(self, role: str, query: str, *, top_k: int = 4) -> list[RetrievedChunk]:
        
        role = role.lower()
        query_vector = self.embedder.embed(query)
        candidates = []
        for record in self.records:
            if record["role"].lower() != role:
                continue
            candidates.append(
                RetrievedChunk(
                    role=record["role"],
                    source=record["source"],
                    chunk_id=record["chunk_id"],
                    text=record["text"],
                    score=cosine_similarity(query_vector, record["embedding"]),
                )
            )
        return sorted(candidates, key=lambda item: item.score, reverse=True)[:top_k]


def read_source(path: Path) -> str:
    if path.suffix.lower() == ".txt":
        return read_text_file(path)
    if path.suffix.lower() == ".pdf":
        try:
            from pypdf import PdfReader

            reader = PdfReader(str(path))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as exc:
            raise RuntimeError(f"Could not read PDF knowledge source {path}: {exc}") from exc
    return ""


vector_store = VectorStore()

