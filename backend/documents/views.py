from rest_framework import viewsets

from .models import Document, RFPDocument
from .serializers import DocumentSerializer, RFPDocumentSerializer


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer


class RFPDocumentViewSet(viewsets.ModelViewSet):
    queryset = RFPDocument.objects.all()
    serializer_class = RFPDocumentSerializer
