from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from .models import Document
from .serializers import DocumentSerializer, DocumentUploadSerializer
import logging

logger = logging.getLogger(__name__)


class DocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Document CRUD operations
    
    Endpoints:
    - GET /api/documents/ - List all documents
    - POST /api/documents/ - Upload a new document
    - GET /api/documents/{id}/ - Retrieve a specific document
    - PUT/PATCH /api/documents/{id}/ - Update a document
    - DELETE /api/documents/{id}/ - Delete a document
    """
    
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get_queryset(self):
        """Filter documents by type if specified"""
        queryset = Document.objects.all()
        doc_type = self.request.query_params.get('type', None)
        
        if doc_type:
            queryset = queryset.filter(document_type=doc_type)
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Handle document upload"""
        logger.info("=" * 80)
        logger.info("DOCUMENT UPLOAD REQUEST RECEIVED")
        logger.info(f"Files in request: {request.FILES.keys()}")
        logger.info(f"Data in request: {request.data.keys()}")
        
        serializer = DocumentUploadSerializer(data=request.data)
        
        if serializer.is_valid():
            logger.info(f"Serializer valid. Document type: {serializer.validated_data.get('document_type', 'knowledge_base')}")
            try:
                document = serializer.save()
                logger.info(f"✓ Document uploaded successfully: {document.name} (ID: {document.id}, Type: {document.document_type})")
                logger.info("=" * 80)
                
                # Return the created document
                response_serializer = DocumentSerializer(
                    document,
                    context={'request': request}
                )
                return Response(
                    response_serializer.data,
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                logger.error(f"✗ Error uploading document: {str(e)}")
                import traceback
                logger.error(f"Traceback:\n{traceback.format_exc()}")
                logger.error("=" * 80)
                return Response(
                    {'error': f'Failed to upload document: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        logger.error(f"✗ Serializer validation failed: {serializer.errors}")
        logger.error("=" * 80)
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    
    def destroy(self, request, *args, **kwargs):
        """Delete a document"""
        instance = self.get_object()
        doc_name = instance.name
        
        try:
            self.perform_destroy(instance)
            logger.info(f"Document deleted: {doc_name}")
            return Response(
                {'message': f'Document "{doc_name}" deleted successfully'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            return Response(
                {'error': f'Failed to delete document: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get document statistics"""
        total_docs = Document.objects.count()
        kb_docs = Document.objects.filter(document_type='knowledge_base').count()
        rfp_docs = Document.objects.filter(document_type='rfp').count()
        processed_docs = Document.objects.filter(processed=True).count()
        
        return Response({
            'total_documents': total_docs,
            'knowledge_base_documents': kb_docs,
            'rfp_documents': rfp_docs,
            'processed_documents': processed_docs,
            'pending_documents': total_docs - processed_docs,
        })
    
    @action(detail=True, methods=['post'])
    def mark_processed(self, request, pk=None):
        """Mark a document as processed"""
        document = self.get_object()
        document.processed = True
        from django.utils import timezone
        document.processed_at = timezone.now()
        document.save()
        
        serializer = self.get_serializer(document)
        return Response(serializer.data)

