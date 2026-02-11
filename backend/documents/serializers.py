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


# ---------------------------------------------------------------------------
# TODO: Add serializers for your Question and Answer models.
# Consider:
#   - A nested serializer that includes questions when retrieving an RFP
#   - A serializer for the answer generation request/response
#   - Validation for file uploads
# ---------------------------------------------------------------------------
