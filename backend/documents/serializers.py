from rest_framework import serializers

from .models import Document, RFPDocument


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ["id", "title", "content", "file_name", "uploaded_at"]
        read_only_fields = ["id", "uploaded_at"]


class RFPDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RFPDocument
        fields = ["id", "title", "content", "file_name", "uploaded_at"]
        read_only_fields = ["id", "uploaded_at"]
