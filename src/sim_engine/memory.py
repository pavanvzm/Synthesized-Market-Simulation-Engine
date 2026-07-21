"""Vector memory module using Qdrant for persona state persistence."""

import hashlib
import json
from typing import Any, Optional

from pydantic import BaseModel


class MemoryRecord(BaseModel):
    """Memory record model."""
    memory_id: str
    persona_id: str
    memory_type: str  # transaction, decision, observation, update
    run_id: str
    round_num: int
    content: str
    embedding: list[float] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class QdrantMemory:
    """Qdrant-backed vector memory for personas.
    
    Supports both local (embedded) and server modes.
    """
    
    def __init__(
        self,
        mode: str = "local",
        host: str = "localhost",
        port: int = 6333,
        collection_name: str = "persona_memory",
        storage_path: str = ".qdrant_storage",
    ):
        """Initialize Qdrant memory.
        
        Args:
            mode: 'local' or 'server'
            host: Qdrant host (server mode)
            port: Qdrant port (server mode)
            collection_name: Collection name
            storage_path: Local storage path (local mode)
        """
        self.mode = mode
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.storage_path = storage_path
        self._client = None
        self._initialized = False
    
    def _get_client(self):
        """Get or create Qdrant client."""
        if self._client is not None:
            return self._client
        
        try:
            from qdrant_client import QdrantClient
            
            if self.mode == "local":
                self._client = QdrantClient(path=self.storage_path)
            else:
                self._client = QdrantClient(host=self.host, port=self.port)
            
            return self._client
        
        except ImportError:
            # Fallback to mock mode if qdrant-client not installed
            return None
    
    def initialize(self) -> bool:
        """Initialize Qdrant collection.
        
        Returns:
            True if successful
        """
        if self._initialized:
            return True
        
        client = self._get_client()
        if client is None:
            # Mock mode - no actual storage
            self._initialized = True
            return True
        
        try:
            from qdrant_client.http import models
            
            # Check if collection exists
            collections = client.get_collections().collections
            if any(c.name == self.collection_name for c in collections):
                self._initialized = True
                return True
            
            # Create collection with payload indexes
            client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE),
            )
            
            # Create payload indexes for filtering
            client.create_payload_index(
                collection_name=self.collection_name,
                field_name="persona_id",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )
            client.create_payload_index(
                collection_name=self.collection_name,
                field_name="memory_type",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )
            client.create_payload_index(
                collection_name=self.collection_name,
                field_name="run_id",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )
            client.create_payload_index(
                collection_name=self.collection_name,
                field_name="round",
                field_schema=models.PayloadSchemaType.INTEGER,
            )
            client.create_payload_index(
                collection_name=self.collection_name,
                field_name="segment",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )
            
            self._initialized = True
            return True
        
        except Exception as e:
            # Fall back to mock mode
            self._initialized = True
            return True
    
    def _generate_embedding(self, text: str) -> list[float]:
        """Generate simple embedding for text.
        
        In production, use a real embedding model.
        For mock mode, use deterministic hash-based vectors.
        """
        # Simple hash-based pseudo-embedding (384 dimensions)
        hash_input = text.encode()
        embedding = []
        for i in range(384):
            h = hashlib.md5(hash_input + bytes([i])).hexdigest()
            # Convert hex to float in [-1, 1]
            val = (int(h[:8], 16) / 0xFFFFFFFF) * 2 - 1
            embedding.append(val)
        
        # Normalize
        norm = sum(x*x for x in embedding) ** 0.5
        if norm > 0:
            embedding = [x/norm for x in embedding]
        
        return embedding
    
    def store(
        self,
        persona_id: str,
        memory_type: str,
        content: str,
        run_id: str,
        round_num: int,
        metadata: Optional[dict[str, Any]] = None,
    ) -> str:
        """Store a memory record.
        
        Args:
            persona_id: Persona identifier
            memory_type: Type of memory
            content: Memory content
            run_id: Simulation run ID
            round_num: Round number
            metadata: Additional metadata
        
        Returns:
            Memory ID
        """
        import uuid
        
        memory_id = f"mem_{uuid.uuid4().hex[:12]}"
        embedding = self._generate_embedding(content)
        
        client = self._get_client()
        if client is None:
            # Mock mode - just return ID
            return memory_id
        
        try:
            from qdrant_client.http import models
            
            payload = {
                "persona_id": persona_id,
                "memory_type": memory_type,
                "run_id": run_id,
                "round": round_num,
                "content": content,
                **(metadata or {}),
            }
            
            client.upsert(
                collection_name=self.collection_name,
                points=[
                    models.PointStruct(
                        id=hash(memory_id) % (2**63),
                        vector=embedding,
                        payload=payload,
                    )
                ],
            )
        
        except Exception:
            pass
        
        return memory_id
    
    def retrieve(
        self,
        persona_id: str,
        top_k: int = 2,
        memory_type: Optional[str] = None,
        run_id: Optional[str] = None,
        round_num: Optional[int] = None,
    ) -> list[MemoryRecord]:
        """Retrieve relevant memories.
        
        Args:
            persona_id: Persona identifier
            top_k: Number of results
            memory_type: Filter by memory type
            run_id: Filter by run ID
            round_num: Filter by round
        
        Returns:
            List of MemoryRecord instances
        """
        client = self._get_client()
        if client is None:
            # Mock mode - return empty
            return []
        
        try:
            from qdrant_client.http import models
            
            # Build filter
            conditions = [
                models.FieldCondition(
                    key="persona_id",
                    match=models.MatchValue(value=persona_id),
                )
            ]
            
            if memory_type:
                conditions.append(
                    models.FieldCondition(
                        key="memory_type",
                        match=models.MatchValue(value=memory_type),
                    )
                )
            
            if run_id:
                conditions.append(
                    models.FieldCondition(
                        key="run_id",
                        match=models.MatchValue(value=run_id),
                    )
                )
            
            if round_num is not None:
                conditions.append(
                    models.FieldCondition(
                        key="round",
                        match=models.MatchValue(value=round_num),
                    )
                )
            
            search_filter = models.Filter(must=conditions)
            
            # Search with dummy query embedding
            query_embedding = self._generate_embedding(persona_id)
            
            results = client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k,
                query_filter=search_filter,
            )
            
            records = []
            for result in results:
                payload = result.payload or {}
                records.append(MemoryRecord(
                    memory_id=f"mem_{result.id}",
                    persona_id=payload.get("persona_id", ""),
                    memory_type=payload.get("memory_type", ""),
                    run_id=payload.get("run_id", ""),
                    round_num=payload.get("round", 0),
                    content=payload.get("content", ""),
                    embedding=result.vector or [],
                    metadata={k: v for k, v in payload.items() if k not in ["persona_id", "memory_type", "run_id", "round", "content"]},
                ))
            
            return records
        
        except Exception:
            return []
    
    def clear(self) -> None:
        """Clear all memories."""
        client = self._get_client()
        if client:
            try:
                client.delete_collection(collection_name=self.collection_name)
                self._initialized = False
            except Exception:
                pass
