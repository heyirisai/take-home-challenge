"""
Vector Store Manager using ChromaDB
Handles document embeddings and semantic search
"""

import os
import logging
from typing import List, Dict, Any, Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class VectorStore:
    """Manages vector embeddings and semantic search using ChromaDB"""
    
    def __init__(self):
        """Initialize ChromaDB client"""
        self._initialized = False
        self.collection = None
        self.client = None
        self.collection_name = "rfp_documents"
        
        try:
            import chromadb
            from chromadb.utils import embedding_functions
            
            vector_db_path = getattr(settings, 'VECTOR_DB_PATH', './vector_store')
            
            # Ensure directory exists
            os.makedirs(vector_db_path, exist_ok=True)
            
            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(path=vector_db_path)
            
            # Use OpenAI embeddings instead of default
            openai_api_key = getattr(settings, 'OPENAI_API_KEY', '')
            if openai_api_key:
                openai_ef = embedding_functions.OpenAIEmbeddingFunction(
                    api_key=openai_api_key,
                    model_name="text-embedding-3-small"  # Faster and cheaper than ada-002
                )
                logger.info("Using OpenAI embeddings (text-embedding-3-small)")
            else:
                # Fallback to default embeddings if no API key
                openai_ef = embedding_functions.DefaultEmbeddingFunction()
                logger.warning("No OpenAI API key - using default embeddings")
            
            # Try to get existing collection, if embedding function conflicts, delete and recreate
            try:
                self.collection = self.client.get_or_create_collection(
                    name=self.collection_name,
                    embedding_function=openai_ef,
                    metadata={"description": "RFP knowledge base documents"}
                )
            except ValueError as e:
                if "embedding function" in str(e).lower():
                    # Delete old collection and create new one with correct embedding function
                    logger.warning(f"Deleting old collection due to embedding function change")
                    try:
                        self.client.delete_collection(self.collection_name)
                    except:
                        pass
                    self.collection = self.client.create_collection(
                        name=self.collection_name,
                        embedding_function=openai_ef,
                        metadata={"description": "RFP knowledge base documents"}
                    )
                else:
                    raise
            
            logger.info(f"ChromaDB collection '{self.collection_name}' initialized")
            self._initialized = True
        except ImportError:
            logger.warning("ChromaDB not available. Install with: pip install chromadb")
        except Exception as e:
            logger.error(f"Error initializing ChromaDB: {str(e)}")
    
    def add_document(
        self,
        document_id: int,
        text_chunks: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add document chunks to vector store
        
        Args:
            document_id: Database ID of the document
            text_chunks: List of text chunks to embed
            metadata: Optional metadata for the document
            
        Returns:
            True if successful, False otherwise
        """
        if not self._initialized:
            logger.error("Vector store not initialized")
            return False
            
        try:
            if not text_chunks:
                logger.warning(f"No text chunks provided for document {document_id}")
                return False
            
            # Create unique IDs for each chunk
            ids = [f"doc_{document_id}_chunk_{i}" for i in range(len(text_chunks))]
            
            # Create metadata for each chunk
            metadatas = []
            for i in range(len(text_chunks)):
                chunk_metadata = {
                    "document_id": document_id,
                    "chunk_index": i,
                    "total_chunks": len(text_chunks)
                }
                if metadata:
                    chunk_metadata.update(metadata)
                metadatas.append(chunk_metadata)
            
            # Add to collection
            self.collection.add(
                ids=ids,
                documents=text_chunks,
                metadatas=metadatas
            )
            
            logger.info(f"Added {len(text_chunks)} chunks for document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding document {document_id} to vector store: {str(e)}")
            return False
    
    def search(
        self,
        query: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant documents using semantic similarity
        
        Args:
            query: Search query
            n_results: Number of results to return
            filter_metadata: Optional metadata filter
            
        Returns:
            List of search results with documents and metadata
        """
        if not self._initialized:
            logger.error("Vector store not initialized")
            return []
            
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=filter_metadata
            )
            
            # Format results
            formatted_results = []
            if results and results['documents']:
                for i in range(len(results['documents'][0])):
                    formatted_results.append({
                        'id': results['ids'][0][i],
                        'document': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i] if 'distances' in results else None
                    })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching vector store: {str(e)}")
            return []
    
    def delete_document(self, document_id: int) -> bool:
        """
        Delete all chunks of a document from vector store
        
        Args:
            document_id: Database ID of the document
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get all chunk IDs for this document
            results = self.collection.get(
                where={"document_id": document_id}
            )
            
            if results and results['ids']:
                self.collection.delete(ids=results['ids'])
                logger.info(f"Deleted {len(results['ids'])} chunks for document {document_id}")
                return True
            else:
                logger.info(f"No chunks found for document {document_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting document {document_id} from vector store: {str(e)}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        try:
            count = self.collection.count()
            return {
                'total_chunks': count,
                'collection_name': self.collection_name
            }
        except Exception as e:
            logger.error(f"Error getting vector store stats: {str(e)}")
            return {'total_chunks': 0, 'collection_name': self.collection_name}
    
    def clear_all(self) -> bool:
        """Clear all documents from vector store (use with caution!)"""
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "RFP knowledge base documents"}
            )
            logger.info(f"Cleared all documents from {self.collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error clearing vector store: {str(e)}")
            return False


# Singleton instance
_vector_store_instance = None


def get_vector_store() -> VectorStore:
    """Get or create vector store singleton instance"""
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStore()
    return _vector_store_instance
