from rest_framework import viewsets

from .models import Document, RFPDocument
from .serializers import DocumentSerializer, RFPDocumentSerializer


class DocumentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for company knowledge-base documents.

    TODO: Consider adding:
      - File upload handling (override create/perform_create)
      - Search/filter functionality
      - A custom action to trigger document processing/chunking
    """

    queryset = Document.objects.all()
    serializer_class = DocumentSerializer


class RFPDocumentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for RFP documents.

    TODO: Consider adding:
      - File upload + automatic question extraction
      - A custom @action to trigger answer generation
      - Status tracking for the generation process
    """

    queryset = RFPDocument.objects.all()
    serializer_class = RFPDocumentSerializer


# ---------------------------------------------------------------------------
# TODO: Add viewsets or API views for:
#   - Questions (list/retrieve, possibly nested under RFP)
#   - Answers (generate, retrieve, update status)
#   - Any custom endpoints your design requires
# ---------------------------------------------------------------------------
