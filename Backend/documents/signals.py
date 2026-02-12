from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Document
from rag_engine.rag_pipeline import get_rag_engine
from rag_engine.vector_store import get_vector_store
from rag_engine.document_extractor import DocumentExtractor
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Document)
def process_document_on_upload(sender, instance, created, **kwargs):
    """
    Process document when uploaded:
    - Extract text
    - Add to vector store (for knowledge base documents)
    """
    if created and instance.document_type == 'knowledge_base':
        try:
            # Extract text and save to model
            if instance.file:
                text = DocumentExtractor.extract_text(instance.file.path)
                if text:
                    instance.extracted_text = text[:10000]  # Store first 10k chars
                    instance.save(update_fields=['extracted_text'])
                    
                    # Process for RAG
                    rag_engine = get_rag_engine()
                    success = rag_engine.process_document_for_rag(
                        instance.file.path,
                        instance.id
                    )
                    
                    if success:
                        instance.processed = True
                        from django.utils import timezone
                        instance.processed_at = timezone.now()
                        instance.save(update_fields=['processed', 'processed_at'])
                        logger.info(f"Document {instance.id} processed successfully")
                else:
                    logger.warning(f"Failed to extract text from document {instance.id}")
        except Exception as e:
            logger.error(f"Error processing document {instance.id}: {str(e)}")


@receiver(post_delete, sender=Document)
def delete_from_vector_store(sender, instance, **kwargs):
    """Remove document from vector store when deleted"""
    if instance.document_type == 'knowledge_base':
        try:
            vector_store = get_vector_store()
            vector_store.delete_document(instance.id)
            logger.info(f"Document {instance.id} removed from vector store")
        except Exception as e:
            logger.error(f"Error removing document {instance.id} from vector store: {str(e)}")
